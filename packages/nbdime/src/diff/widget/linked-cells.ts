import { Panel, Widget } from "@lumino/widgets";
import type { CellDiffWidget } from "./";
import { LabIcon }  from "@jupyterlab/ui-components";

import foldDown from "./fold-down.svg";
import foldUp from "./fold-up.svg";
import fold from "./fold.svg";

export const foldDownIcon = new LabIcon({
  name: "nbdime:fold-down",
  svgstr: foldDown
});

export const foldUpIcon = new LabIcon({
  name: "nbdime:fold-up",
  svgstr: foldUp
});

export const foldIcon = new LabIcon({
  name: "nbdime:fold",
  svgstr: fold
});

export interface ILinkedListCell {
  next: () => ILinkedListCell | null;
  prev: () => ILinkedListCell | null;
  displayed: () => boolean;
  lazy: boolean;
  expandUp: () => void;
  expandDown: () => void;
}

class LinkedListCell extends Panel {
  _next: LinkedListCell | LazyDisplayLinkedListCell | null;
  _prev: LinkedListCell | LazyDisplayLinkedListCell | null;
  renderFunc: () => CellDiffWidget;
  _displayed: boolean;
  lazy: boolean;

  constructor(renderFunc: () => CellDiffWidget) {
    super();
    this._next = null;
    this._prev = null;
    this.renderFunc = renderFunc;
    this._displayed = true;
    this.renderCell();
    this.addClass("linked-cell");
    this.lazy = false;
  }

  protected renderCell() {
    this.addWidget(this.renderFunc());
    this._displayed = true;
  }

  get next(): LinkedListCell | LazyDisplayLinkedListCell | null {
    return this._next;
  }

  set next(nextCell: LinkedListCell | LazyDisplayLinkedListCell | null) {
    this._next = nextCell;
    if (nextCell === null) {
      return;
    }

    if (nextCell.lazy) {
      nextCell.expandDown();
    }
  }

  get prev(): LinkedListCell | LazyDisplayLinkedListCell | null {
    return this._prev;
  }

  set prev(prevCell: LinkedListCell | LazyDisplayLinkedListCell | null) {
    this._prev = prevCell;
    if (prevCell === null) {
      return;
    }
    prevCell.next = this;
    if (prevCell.lazy) {
      prevCell.expandUp();
    }
  }

  get displayed(): boolean {
    return this._displayed;
  }

  expandUp(): void {
    return;
  }

  expandDown(): void {
    return;
  }
}

class LazyDisplayLinkedListCell extends LinkedListCell {
  expandButton: HTMLDivElement;
  expandButtonDisplayed: boolean;

  // Path: packages/nbdime/src/diff/widget/wrapper_cells.ts
  constructor(renderFunc: () => CellDiffWidget) {
    super(renderFunc);
    this.expandButton = document.createElement("div");
    this.expandButton.className = "jp-expand-output-wrapper";
    this.expandButtonDisplayed = false;
    this.addClass("lazy-linked-cell");
    this.lazy = true;
  }

  set prev(prevCell: LinkedListCell | LazyDisplayLinkedListCell) {
    this._prev = prevCell;
    prevCell.next = this;
  }

  set next(nextCell: LinkedListCell | LazyDisplayLinkedListCell) {
    this._next = nextCell;
  }

  protected renderCell() {
    this._displayed = false;
  }

  expandUp(): void {
    if (this._displayed) {
      return;
    }
    if (this.expandButtonDisplayed) {
      this._setupFoldButton();
    } else {
      this._setupExpandUpButton();
    }
  }

  expandDown(): void {
    if (this._displayed) {
      return;
    }
    if (this.expandButtonDisplayed) {
      this._setupFoldButton();
    } else {
      this._setupExpandDownButton();
    }
  }

  _setupFoldButton() {
    this.expandButton.innerHTML = "";
    const button = this.createButton("Fold");
    button.onclick = (e) => {
      e.preventDefault();
      this.showLazyCellUp();
    };
    this.expandButton.appendChild(button);
    const widget = new Widget({ node: this.expandButton });
    this.addWidget(widget);
  }

  _setupExpandUpButton() {
    const button = this.createButton("Up");
    button.onclick = (e) => {
      e.preventDefault();
      this.showLazyCellUp();
    };
    this.expandButton.appendChild(button);
    const widget = new Widget({ node: this.expandButton });
    this.addWidget(widget);
  }

  _setupExpandDownButton() {
    const button = this.createButton("Down");
    button.onclick = (e) => {
      e.preventDefault();
      this.showLazyCellDown();
    };
    this.expandButton.appendChild(button);
    const widget = new Widget({ node: this.expandButton });
    this.addWidget(widget);
  }

  createButton(direction: "Up" | "Down" | "Fold"): HTMLAnchorElement {
    this.expandButton.innerHTML = "";
    const button = document.createElement("a");
    button.title = `Expand ${direction}`;
    button.setAttribute("aria-label", `Expand ${direction}`);
    let icon = this.buttonSvg(direction);
    icon.element({
      container: button,
    })
    this.expandButtonDisplayed = true;
    return button;
  }

  buttonSvg(direction: "Up" | "Down" | "Fold"): LabIcon {
    if (direction === "Up") {
      return foldUp;
    } else if (direction === "Down") {
      return foldDown;
    } else {
      return fold;
    }
  }

  showLazyCellUp() {
    this.showLazyCell();
    this._prev?.expandUp();
  }

  showLazyCellDown() {
    this.showLazyCell();
    this._next?.expandDown();
  }

  showLazyCell() {
    this.addWidget(this.renderFunc());
    this._displayed = true;
    this.expandButton.remove();
  }
}

export { LinkedListCell, LazyDisplayLinkedListCell };
