import { createAddedCellDiffModel } from "../../../../src/diff/model";
import { CellDiffWidget } from "../../../../src/diff/widget";
import * as nbformat from "@jupyterlab/nbformat";
import {
  LazyDisplayLinkedListCell,
  LinkedListCell,
} from "../../../../src/diff/widget/linked-cells";

import {
  RenderMimeRegistry,
  standardRendererFactories,
} from "@jupyterlab/rendermime";

let codeCellA: nbformat.ICodeCell = {
  cell_type: "code",
  execution_count: 2,
  metadata: {
    collapsed: false,
    trusted: false,
  },
  outputs: [],
  source: "l = f(3, 4)\nprint(l)",
};

function renderFunc() {
  let mimetype = "text/python";
  let model = createAddedCellDiffModel(codeCellA, mimetype);
  let rendermime = new RenderMimeRegistry({
    initialFactories: standardRendererFactories,
  });

  return new CellDiffWidget(model, rendermime, mimetype);
}

// JSDOM Does not properly support createRange in the version we are using
// This patches it https://github.com/jsdom/jsdom/issues/3002
document.createRange = () => {
  const range = new Range();

  range.getBoundingClientRect = jest.fn();

  range.getClientRects = jest.fn(() => ({
    item: () => null,
    length: 0,
  }));

  return range;
};

let emptyCell = `<div class=\"lm-Widget p-Widget lm-Panel p-Panel jp-Cell-diff jp-Diff-added\"><div class=\"lm-Widget p-Widget lm-Panel p-Panel jp-Cellrow-source\"><div class=\"lm-Widget p-Widget lm-Panel p-Panel p-mod-left-to-right p-FlexPanel jp-Cellrow-executionCount\"><div class=\"lm-Widget p-Widget jp-InputPrompt p-FlexPanel-child\" style=\"flex-grow: 1;\"></div></div><div class=\"lm-Widget p-Widget lm-Panel p-Panel CodeMirror-merge CodeMirror-merge-1pane\"><div class=\"lm-Widget p-Widget jp-CodeMirrorEditor jp-Editor CodeMirror-merge-pane CodeMirror-merge-pane-base CodeMirror-merge-pane-added\" data-type=\"inline\"><div class=\"CodeMirror jp-mod-readOnly cm-s-jupyter CodeMirror-wrap\"><div style=\"overflow: hidden; position: relative; width: 3px; height: 0px; top: 0px; left: 0px;\"><textarea style=\"position: absolute; bottom: -1em; padding: 0px; width: 1000px; height: 1em; outline: none;\" autocorrect=\"off\" autocapitalize=\"off\" spellcheck=\"false\" readonly=\"\" tabindex=\"0\"></textarea></div><div class=\"CodeMirror-vscrollbar\" tabindex=\"-1\" cm-not-content=\"true\" style=\"display: block; bottom: 0px;\"><div style=\"min-width: 1px; height: 55px;\"></div></div><div class=\"CodeMirror-hscrollbar\" tabindex=\"-1\" cm-not-content=\"true\"><div style=\"height: 100%; min-height: 1px; width: 0px;\"></div></div><div class=\"CodeMirror-scrollbar-filler\" cm-not-content=\"true\"></div><div class=\"CodeMirror-gutter-filler\" cm-not-content=\"true\"></div><div class=\"CodeMirror-scroll\" tabindex=\"-1\"><div class=\"CodeMirror-sizer\" style=\"margin-left: 0px; padding-right: 0px; padding-bottom: 0px;\"><div style=\"position: relative;\"><div class=\"CodeMirror-lines\" role=\"presentation\"><div style=\"position: relative; outline: none;\" role=\"presentation\"><div class=\"CodeMirror-measure\"></div><div class=\"CodeMirror-measure\"><pre class=\"CodeMirror-line\" role=\"presentation\"><span style=\"padding-right: .1px;\" role=\"presentation\">l = f(3, 4)</span></pre></div><div style=\"position: relative; z-index: 1;\"></div><div class=\"CodeMirror-cursors\"></div><div class=\"CodeMirror-code\" role=\"presentation\"></div></div></div></div></div><div style=\"position: absolute; height: 50px; width: 1px; border-bottom: 0px solid transparent;\"></div><div class=\"CodeMirror-gutters\" style=\"left: 0px;\"><div class=\"CodeMirror-gutter CodeMirror-linenumbers\" style=\"width: 1px;\"></div></div></div></div></div><div class=\"CodeMirror-merge-clear lm-Widget p-Widget\" style=\"height: 0px; clear: both;\"></div></div></div><div class=\"lm-Widget p-Widget lm-Panel p-Panel jp-CollapsiblePanel jp-Cellrow-metadata\"><div class=\"lm-Widget p-Widget lm-Panel p-Panel jp-CollapsiblePanel-header\"><button class=\"jp-CollapsiblePanel-header-icon jp-CollapsiblePanel-header-icon-closed fa fa-caret-down\"></button></div><div class=\"lm-Widget p-Widget lm-Panel p-Panel jp-CollapsiblePanel-container\"><div class=\"lm-Widget p-Widget lm-Panel p-Panel jp-CollapsiblePanel-slider jp-CollapsiblePanel-closed\"><div class=\"lm-Widget p-Widget lm-Panel p-Panel CodeMirror-merge CodeMirror-merge-1pane\"><div class=\"lm-Widget p-Widget jp-CodeMirrorEditor jp-Editor CodeMirror-merge-pane CodeMirror-merge-pane-base CodeMirror-merge-pane-added\" data-type=\"inline\"><div class=\"CodeMirror jp-mod-readOnly cm-s-jupyter CodeMirror-wrap\"><div style=\"overflow: hidden; position: relative; width: 3px; height: 0px; top: 0px; left: 0px;\"><textarea style=\"position: absolute; bottom: -1em; padding: 0px; width: 1000px; height: 1em; outline: none;\" autocorrect=\"off\" autocapitalize=\"off\" spellcheck=\"false\" readonly=\"\" tabindex=\"0\"></textarea></div><div class=\"CodeMirror-vscrollbar\" tabindex=\"-1\" cm-not-content=\"true\" style=\"display: block; bottom: 0px;\"><div style=\"min-width: 1px; height: 61px;\"></div></div><div class=\"CodeMirror-hscrollbar\" tabindex=\"-1\" cm-not-content=\"true\"><div style=\"height: 100%; min-height: 1px; width: 0px;\"></div></div><div class=\"CodeMirror-scrollbar-filler\" cm-not-content=\"true\"></div><div class=\"CodeMirror-gutter-filler\" cm-not-content=\"true\"></div><div class=\"CodeMirror-scroll\" tabindex=\"-1\"><div class=\"CodeMirror-sizer\" style=\"margin-left: 0px; padding-right: 0px; padding-bottom: 0px;\"><div style=\"position: relative;\"><div class=\"CodeMirror-lines\" role=\"presentation\"><div style=\"position: relative; outline: none;\" role=\"presentation\"><div class=\"CodeMirror-measure\"></div><div class=\"CodeMirror-measure\"><pre class=\"CodeMirror-line\" role=\"presentation\"><span style=\"padding-right: .1px;\" role=\"presentation\"><span class=\" CodeMirror-matchingbracket\">{</span></span></pre></div><div style=\"position: relative; z-index: 1;\"></div><div class=\"CodeMirror-cursors\"></div><div class=\"CodeMirror-code\" role=\"presentation\"></div></div></div></div></div><div style=\"position: absolute; height: 50px; width: 1px; border-bottom: 0px solid transparent;\"></div><div class=\"CodeMirror-gutters\" style=\"left: 0px;\"><div class=\"CodeMirror-gutter CodeMirror-linenumbers\" style=\"width: 1px;\"></div></div></div></div></div><div class=\"CodeMirror-merge-clear lm-Widget p-Widget\" style=\"height: 0px; clear: both;\"></div></div></div></div></div></div>`;

describe("linked cells", () => {
  describe("has a linked list shape with a cell", () => {
    it("has a previous and next neighbor", () => {
      const cell = new LinkedListCell(renderFunc);
      expect(cell.prev).toBeNull();
      expect(cell.next).toBeNull();
      const next = new LinkedListCell(renderFunc);
      next.prev = cell;
      expect(cell.next).toBe(next);
      expect(next.prev).toBe(cell);
      const previous = new LinkedListCell(renderFunc);
      cell.prev = previous;
      expect(cell.prev).toBe(previous);
      expect(previous.next).toBe(cell);
    });
  });

  it("starts displayed when not lazy", () => {
    const cell = new LinkedListCell(renderFunc);
    expect(cell.displayed).toBe(true);
    expect(cell.node.innerHTML.toString()).toBe(emptyCell);
  });

  describe("lazy linked list cells", () => {
    it("can call the callback render function", () => {
      const cell = new LazyDisplayLinkedListCell(renderFunc);
      expect(cell.displayed).toBe(false);
      expect(cell.node.innerHTML.toString()).toBe("");
      cell.showLazyCell();
      expect(cell.displayed).toBe(true);
      expect(cell.node.innerHTML.toString()).toBe(emptyCell);
    });

    it("show the expand down button when added to a non-lazy previous cell", () => {
      const cell = new LazyDisplayLinkedListCell(renderFunc);
      const previous = new LinkedListCell(renderFunc);
      cell.prev = previous;
      expect(cell.node.innerHTML.toString()).toContain("Expand Down");
      expect(cell.node.innerHTML.toString()).not.toContain("Expand Up");
    });

    it("show the expand up button when added to a non-lazy next cell", () => {
      const cell = new LazyDisplayLinkedListCell(renderFunc);
      const next = new LinkedListCell(renderFunc);
      next.prev = cell;
      expect(cell.node.innerHTML.toString()).toContain("Expand Up");
      expect(cell.node.innerHTML.toString()).not.toContain("Expand Down");
    });

    it("triggering the expand up button calls show expand up on the previous cell", () => {
      const shown = new LinkedListCell(renderFunc);
      const prev = new LazyDisplayLinkedListCell(renderFunc);
      const toBeCalled = new LazyDisplayLinkedListCell(renderFunc);
      shown.prev = prev;
      prev.prev = toBeCalled;

      const spy = jest.spyOn(toBeCalled, "expandUp");
      const noSpy = jest.spyOn(toBeCalled, "expandDown");
      const noRenderSpy = jest.spyOn(toBeCalled, "showLazyCell");
      const renderSpy = jest.spyOn(prev, "showLazyCell");

      prev.showLazyCellUp();
      expect(renderSpy).toHaveBeenCalled();
      expect(noSpy).not.toHaveBeenCalled();
      expect(spy).toHaveBeenCalled();
      expect(noRenderSpy).not.toHaveBeenCalled();
    });

    it("triggering the expand down button calls show expand down on the next cell", () => {
      const shown = new LinkedListCell(renderFunc);
      const next = new LazyDisplayLinkedListCell(renderFunc);
      const toBeCalled = new LazyDisplayLinkedListCell(renderFunc);
      shown.next = next;
      next.next = toBeCalled;

      const renderSpy = jest.spyOn(next, "showLazyCell");
      const noRenderSpy = jest.spyOn(toBeCalled, "showLazyCell");
      const spy = jest.spyOn(toBeCalled, "expandDown");
      const noSpy = jest.spyOn(toBeCalled, "expandUp");
      next.showLazyCellDown();
      expect(renderSpy).toHaveBeenCalled();
      expect(spy).toHaveBeenCalled();
      expect(noSpy).not.toHaveBeenCalled();
      expect(noRenderSpy).not.toHaveBeenCalled();
    });

    it("show a fold icon if the above and below cells are displayed", () => {
      const shownTop = new LinkedListCell(renderFunc);
      const shownBottom = new LinkedListCell(renderFunc);
      const lazy = new LazyDisplayLinkedListCell(renderFunc);
      lazy.prev = shownTop;
      shownBottom.prev = lazy;
      expect(lazy.node.innerHTML.toString()).toContain("Fold");
    });

    it("shows a fold icon if the above and below cells are lazy and opened", () => {
      const lazyTop = new LazyDisplayLinkedListCell(renderFunc);
      const lazyBottom = new LazyDisplayLinkedListCell(renderFunc);
      const LazyMiddle = new LazyDisplayLinkedListCell(renderFunc);
      LazyMiddle.prev = lazyTop;
      lazyBottom.prev = LazyMiddle;

      lazyTop.showLazyCellDown();
      lazyBottom.showLazyCellUp();
      expect(LazyMiddle.node.innerHTML.toString()).toContain("Fold");
    });
  });
});
