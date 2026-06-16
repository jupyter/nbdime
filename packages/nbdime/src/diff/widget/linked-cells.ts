import { Panel, Widget } from '@lumino/widgets';
import type { CellDiffWidget } from './';
import { LabIcon } from '@jupyterlab/ui-components';

import foldDown from './fold-down.svg';
import foldUp from './fold-up.svg';
import fold from './fold.svg';

export const foldDownIcon = new LabIcon({
  name: 'nbdime:fold-down',
  svgstr: foldDown,
});

export const foldUpIcon = new LabIcon({
  name: 'nbdime:fold-up',
  svgstr: foldUp,
});

export const foldIcon = new LabIcon({
  name: 'nbdime:fold',
  svgstr: fold,
});

export interface ILinkedListCell {
  _next: ILinkedListCell | null;
  _prev: ILinkedListCell | null;
  displayed: boolean;
  lazy: boolean;
  expandUp: () => void;
  expandDown: () => void;
}

class LinkedListCell extends Panel implements ILinkedListCell {
  renderFunc: () => CellDiffWidget;
  displayed: boolean;
  _next: ILinkedListCell | null;
  _prev: ILinkedListCell | null;
  lazy: boolean;

  constructor(renderFunc: () => CellDiffWidget) {
    super();
    this._next = null;
    this._prev = null;
    this.renderFunc = renderFunc;
    this.displayed = true;
    this.renderCell();
    this.addClass('linked-cell');
    this.lazy = false;
  }

  protected renderCell() {
    this.addWidget(this.renderFunc());
    this.displayed = true;
  }

  get next() {
    return this._next;
  }

  set next(nextCell) {
    this._next = nextCell;
    if (nextCell === null) {
      return;
    }

    if (nextCell.lazy) {
      nextCell.expandDown();
    }
  }

  get prev() {
    return this._prev;
  }

  set prev(prevCell) {
    this._prev = prevCell;
    if (prevCell === null) {
      return;
    }
    prevCell._next = this as ILinkedListCell;
    if (prevCell.lazy) {
      prevCell.expandUp();
    }
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
    this.expandButton = document.createElement('div');
    this.expandButton.className = 'jp-expand-output-wrapper';
    this.expandButtonDisplayed = false;
    this.addClass('lazy-linked-cell');
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
    this.displayed = false;
  }

  expandUp(): void {
    if (this.displayed) {
      return;
    }
    if (this.expandButtonDisplayed) {
      this._setupFoldButton();
    } else {
      this._setupExpandUpButton();
    }
  }

  expandDown(): void {
    if (this.displayed) {
      return;
    }
    if (this.expandButtonDisplayed) {
      this._setupFoldButton();
    } else {
      this._setupExpandDownButton();
    }
  }

  _setupFoldButton() {
    this.expandButton.innerHTML = '';
    const button = this.createButton('Fold');
    button.onclick = e => {
      e.preventDefault();
      this.showLazyCellUp();
    };
    this.expandButton.appendChild(button);
    const widget = new Widget({ node: this.expandButton });
    this.addWidget(widget);
  }

  _setupExpandUpButton() {
    const button = this.createButton('Up');
    button.onclick = e => {
      e.preventDefault();
      this.showLazyCellUp();
    };
    this.expandButton.appendChild(button);
    const widget = new Widget({ node: this.expandButton });
    this.addWidget(widget);
  }

  _setupExpandDownButton() {
    const button = this.createButton('Down');
    button.onclick = e => {
      e.preventDefault();
      this.showLazyCellDown();
    };
    this.expandButton.appendChild(button);
    const widget = new Widget({ node: this.expandButton });
    this.addWidget(widget);
  }

  createButton(direction: 'Up' | 'Down' | 'Fold'): HTMLAnchorElement {
    this.expandButton.innerHTML = '';
    const button = document.createElement('a');
    button.title = `Expand ${direction}`;
    button.setAttribute('aria-label', `Expand ${direction}`);
    let icon = this.buttonSvg(direction);
    icon.element({
      container: button,
    });
    this.expandButtonDisplayed = true;
    return button;
  }

  buttonSvg(direction: 'Up' | 'Down' | 'Fold'): LabIcon {
    if (direction === 'Up') {
      return foldUpIcon;
    } else if (direction === 'Down') {
      return foldDownIcon;
    } else {
      return foldIcon;
    }
  }

  showLazyCellUp() {
    this.showLazyCell();
    if (this._prev) {
      this._prev.expandUp();
    }
  }

  showLazyCellDown() {
    this.showLazyCell();
    if (this._next) {
      this._next.expandDown();
    }
  }

  showLazyCell() {
    this.addWidget(this.renderFunc());
    this.displayed = true;
    this.expandButton.remove();
  }
}

export { LinkedListCell, LazyDisplayLinkedListCell };
