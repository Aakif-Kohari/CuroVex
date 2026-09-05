"""Trains a GAT link-prediction model on the CuroVex knowledge graph.

Uses pre-trained KG embeddings (from benchmark_embeddings.py) as initial
node features, then trains a Graph Attention Network for link prediction.

Usage:
    python train_gat.py
    python train_gat.py --epochs 200 --lr 0.001 --hidden-dim 128
"""

import argparse
from pathlib import Path

import mlflow
import torch
import torch.nn.functional as F
from dotenv import load_dotenv
from graph_utils import build_pyg_data, get_default_csv_paths, load_triples_from_csv
from sklearn.metrics import average_precision_score, roc_auc_score
from torch import nn
from torch_geometric.nn import GATConv
from torch_geometric.transforms import RandomLinkSplit

load_dotenv()


class GATLinkPredictor(nn.Module):
    def __init__(self, in_dim: int, hidden_dim: int, out_dim: int, heads: int = 4):
        super().__init__()
        self.conv1 = GATConv(in_dim, hidden_dim, heads=heads, concat=True)
        self.conv2 = GATConv(hidden_dim * heads, out_dim, heads=1, concat=False)

    def encode(self, x, edge_index):
        x = F.elu(self.conv1(x, edge_index))
        x = self.conv2(x, edge_index)
        return x

    def decode(self, z, edge_index):
        # Dot product decoder
        return (z[edge_index[0]] * z[edge_index[1]]).sum(dim=-1)

    def forward(self, x, edge_index):
        z = self.encode(x, edge_index)
        return z


def train():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=200)
    parser.add_argument("--lr", type=float, default=0.001)
    parser.add_argument("--hidden-dim", type=int, default=128)
    parser.add_argument("--device", type=str, default="auto")
    parser.add_argument("--data-dir", type=str, default="")
    args = parser.parse_args()

    if args.device == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(args.device)

    if args.data_dir:
        data_dir = Path(args.data_dir)
        nodes_path = data_dir / "nodes.csv"
        edges_path = data_dir / "edges.csv"
    else:
        nodes_path, edges_path = get_default_csv_paths()

    triples_factory = load_triples_from_csv(nodes_path, edges_path)
    embeddings_path = Path("artifacts/best_embeddings.pt")
    if not embeddings_path.exists():
        raise FileNotFoundError(
            f"{embeddings_path} not found. Run benchmark_embeddings.py first."
        )

    entity_embeddings = torch.load(embeddings_path)
    if entity_embeddings.is_complex():
        entity_embeddings = torch.view_as_real(entity_embeddings).flatten(1)
    data = build_pyg_data(triples_factory, entity_embeddings)

    transform = RandomLinkSplit(
        num_val=0.1, num_test=0.1, is_undirected=False, add_negative_train_samples=True
    )

    train_data, val_data, _ = transform(data)

    train_data = train_data.to(device)
    val_data = val_data.to(device)

    in_dim = entity_embeddings.shape[1]
    model = GATLinkPredictor(
        in_dim=in_dim, hidden_dim=args.hidden_dim, out_dim=in_dim
    ).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    criterion = nn.BCEWithLogitsLoss()

    mlflow.set_experiment("curovex-gat-training")

    best_val_auc = 0
    output_dir = Path("artifacts")
    output_dir.mkdir(parents=True, exist_ok=True)

    with mlflow.start_run():
        mlflow.log_params(vars(args))

        for epoch in range(1, args.epochs + 1):
            model.train()
            optimizer.zero_grad()

            z = model.encode(train_data.x, train_data.edge_index)

            edge_label_index = train_data.edge_label_index
            edge_label = train_data.edge_label

            out = model.decode(z, edge_label_index)
            loss = criterion(out, edge_label.float())

            loss.backward()
            optimizer.step()

            if epoch % 10 == 0:
                model.eval()
                with torch.no_grad():
                    z_val = model.encode(val_data.x, val_data.edge_index)
                    out_val = model.decode(z_val, val_data.edge_label_index)

                    y_pred = torch.sigmoid(out_val).cpu().numpy()
                    y_true = val_data.edge_label.cpu().numpy()

                    val_auc = roc_auc_score(y_true, y_pred)
                    val_ap = average_precision_score(y_true, y_pred)

                    mlflow.log_metric("train_loss", loss.item(), step=epoch)
                    mlflow.log_metric("val_auc", val_auc, step=epoch)
                    mlflow.log_metric("val_ap", val_ap, step=epoch)

                    if val_auc > best_val_auc:
                        best_val_auc = val_auc
                        torch.save(
                            model.state_dict(), output_dir / "gat_link_predictor.pt"
                        )


def main():
    train()


if __name__ == "__main__":
    main()
