import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import ExplanationToggle from "@/components/ExplanationToggle";

// Mock framer-motion
jest.mock("framer-motion", () => ({
  motion: {
    // Strip out layoutId, initial, animate, exit so React doesn't complain
    div: ({ children, layoutId, initial, animate, exit, ...props }: any) => (
      <div {...props}>{children}</div>
    ),
    button: ({ children, layoutId, initial, animate, exit, ...props }: any) => (
      <button {...props}>{children}</button>
    ),
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

describe("ExplanationToggle", () => {
  it("renders both tabs", () => {
    render(
      <ExplanationToggle activeMethod="path_based" onToggle={jest.fn()} />,
    );
    expect(screen.getByText("Path-Based")).toBeInTheDocument();
    expect(screen.getByText("Counterfactual")).toBeInTheDocument();
  });

  it("calls onToggle with counterfactual when clicked", () => {
    const onToggle = jest.fn();
    render(<ExplanationToggle activeMethod="path_based" onToggle={onToggle} />);

    fireEvent.click(screen.getByText("Counterfactual"));
    expect(onToggle).toHaveBeenCalledWith("counterfactual");
  });

  it("calls onToggle with path_based when clicked", () => {
    const onToggle = jest.fn();
    render(
      <ExplanationToggle activeMethod="counterfactual" onToggle={onToggle} />,
    );

    fireEvent.click(screen.getByText("Path-Based"));
    expect(onToggle).toHaveBeenCalledWith("path_based");
  });

  it("highlights the active tab", () => {
    const { container } = render(
      <ExplanationToggle activeMethod="counterfactual" onToggle={jest.fn()} />,
    );
    // The active tab should have teal color styling
    const counterfactualBtn = screen.getByText("Counterfactual");
    expect(counterfactualBtn.className).toContain("text-teal-400");
  });
});
