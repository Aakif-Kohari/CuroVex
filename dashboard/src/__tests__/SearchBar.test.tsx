import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import SearchBar from "@/components/SearchBar";

describe("SearchBar", () => {
  it("renders the search input", () => {
    render(<SearchBar onSearch={jest.fn()} />);
    expect(
      screen.getByPlaceholderText(/search by disease/i),
    ).toBeInTheDocument();
  });

  it("renders the search button", () => {
    render(<SearchBar onSearch={jest.fn()} />);
    expect(screen.getByRole("button", { name: /search/i })).toBeInTheDocument();
  });

  it("calls onSearch with trimmed query on submit", () => {
    const onSearch = jest.fn();
    render(<SearchBar onSearch={onSearch} />);

    const input = screen.getByPlaceholderText(/search by disease/i);
    fireEvent.change(input, { target: { value: "  Diabetes  " } });
    fireEvent.submit(input.closest("form")!);

    expect(onSearch).toHaveBeenCalledWith("Diabetes");
  });

  it("does not call onSearch with empty query", () => {
    const onSearch = jest.fn();
    render(<SearchBar onSearch={onSearch} />);

    fireEvent.submit(
      screen.getByPlaceholderText(/search by disease/i).closest("form")!,
    );
    expect(onSearch).not.toHaveBeenCalled();
  });

  it("disables input when isLoading is true", () => {
    render(<SearchBar onSearch={jest.fn()} isLoading={true} />);
    expect(screen.getByPlaceholderText(/search by disease/i)).toBeDisabled();
  });

  it("shows loading state when isLoading", () => {
    render(<SearchBar onSearch={jest.fn()} isLoading={true} />);
    expect(screen.getByText(/searching/i)).toBeInTheDocument();
  });
});
