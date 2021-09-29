

import * as nbformat from '@jupyterlab/nbformat';

import {
  IRenderMimeRegistry
} from '@jupyterlab/rendermime';

import {
  ServerConnection
} from '@jupyterlab/services';

import {
  JSONObject
} from '@lumino/coreutils';

import {
  Message
} from '@lumino/messaging';

import {
  Widget, Panel
} from '@lumino/widgets';

import {
  IDiffEntry
} from 'nbdime/lib/diff/diffentries';

import {
  NotebookDiffModel
} from 'nbdime/lib/diff/model';

import {
  NotebookDiffWidget, CELLDIFF_CLASS
} from 'nbdime/lib/diff/widget';

import {
  UNCHANGED_DIFF_CLASS, CHUNK_PANEL_CLASS
} from 'nbdime/lib/diff/widget/common';

import {
  requestApiJson
} from 'nbdime/lib/request';



/**
 * Class of the outermost widget, the draggable tab
 */
const NBDIME_CLASS = 'nbdime-Widget'

/**
 * Class of the root of the actual diff, the scroller element
 */
const ROOT_CLASS = 'nbdime-root'

/**
 * DOM class for whether or not to hide unchanged cells
 */
const HIDE_UNCHANGED_CLASS = 'jp-mod-hideUnchanged';


export
class NbdimeWidget extends Panel {
  /**
   *
   */
  constructor(options: NbdimeWidget.IOptions) {
    super();

    this.addClass(NBDIME_CLASS);

    this.base = options.base;
    this.remote = options.remote;
    this.rendermime = options.rendermime;

    let header = Private.diffHeader(options);
    this.addWidget(header);

    this.scroller = new Panel();
    this.scroller.addClass(ROOT_CLASS);
    this.scroller.node.tabIndex = -1;
    this.addWidget(this.scroller);

    let hideUnchangedChk = header.node.getElementsByClassName('nbdime-hide-unchanged')[0] as HTMLInputElement;
    hideUnchangedChk.checked = options.hideUnchanged === undefined
      ? true : options.hideUnchanged;
    hideUnchangedChk.onchange = () => {
      Private.toggleShowUnchanged(this.scroller, !hideUnchangedChk.checked);
    };
    if (options.hideUnchanged) {
      Private.toggleShowUnchanged(this.scroller, false);
    }

    let args: JSONObject;
    if (this.remote) {
      args = {base: this.base, remote: this.remote};
    } else if (options.baseLabel === 'Checkpoint') {
      args = {base: `checkpoint:${this.base}`}
    } else {
      args = {base: `git:${this.base}`}
    }

    requestApiJson(
      ServerConnection.makeSettings().baseUrl,
      'nbdime/api/diff',
      args,
      this.onData.bind(this),
      this.onError.bind(this));
    this.id = `nbdime-${JSON.stringify(args)}`;
    this.title.closable = true;
    return this;
  }

  dispose(): void {
    super.dispose();
    this.rendermime = null!;
    this.header = null!;
    this.scroller = null!;
  }

  /**
   * Handle `'activate-request'` messages.
   */
  protected onActivateRequest(msg: Message): void {
    this.scroller.node.focus();
  }


  protected onData(data: JSONObject) {
    if (this.isDisposed) {
      return;
    }
    let base = data['base'] as nbformat.INotebookContent;
    let diff = data['diff'] as any as IDiffEntry[];
    let nbdModel = new NotebookDiffModel(base, diff);
    let nbdWidget = new NotebookDiffWidget(nbdModel, this.rendermime);

    this.scroller.addWidget(nbdWidget);
    let work = nbdWidget.init();
    work.then(() => {
      Private.markUnchangedRanges(this.scroller.node);
    })
    return work;
  }

  protected onError(error: ServerConnection.NetworkError | ServerConnection.ResponseError): void {
    if (this.isDisposed) {
      return;
    }
    let widget = new Widget();
    widget.node.innerHTML = `Failed to fetch diff: ${error.message}`;
    this.scroller.addWidget(widget);
  }

  readonly base: string;
  readonly remote: string | undefined;

  protected rendermime: IRenderMimeRegistry;

  protected header: Widget;
  protected scroller: Panel;
}


export
namespace NbdimeWidget {

  export
  interface IOptions {
    /**
     * The base notebook path.
     */
    base: string,

    /**
     * The remote notebook path. If undefined, base will be diffed against git HEAD.
     */
    remote?: string,

    /**
     * A rendermime instance to use to render markdown/outputs.
     */
    rendermime: IRenderMimeRegistry,

    /**
     * If specified this will be use to represent the base file in the view.
     *
     * Defaults to the value of `base`.
     *
     * Note: The labels will be ignored for git diffs.
     */
    baseLabel?: string,

    /**
     * If specified this will be use to represent the remote file in the view.
     *
     * Defaults to the value of `remote`.
     *
     * Note: The labels will be ignored for git diffs.
     */
    remoteLabel?: string,

    /**
     * Whether to hide unchanged cells by default.
     */
    hideUnchanged?: boolean,
  }
}


namespace Private {

  /**
   * Create a header widget for the diff view.
   */
  export
  function diffHeader(options: NbdimeWidget.IOptions): Widget {
    let {base, remote, baseLabel, remoteLabel} = options;
    if (remote) {
      if (baseLabel === undefined) {
        baseLabel = base;
      }
      if (remoteLabel === undefined) {
        remoteLabel = remote;
      }
    } else {
      if (!baseLabel) {
        baseLabel = 'git HEAD';
      }
      remoteLabel = base;
    }

    let node = document.createElement('div');
    node.className = 'nbdime-Diff';
    node.innerHTML = `
      <div class="nbdime-header-buttonrow">
        <label><input class="nbdime-hide-unchanged" type="checkbox">Hide unchanged cells</label>
        <button class="nbdime-export" style="display: none">Export diff</button>
      </div>
      <div class=nbdime-header-banner>
        <span class="nbdime-header-base"></span>
        <span class="nbdime-header-remote"></span>
      </div>`;
    (node.getElementsByClassName("nbdime-header-base")[0] as HTMLSpanElement).innerText = baseLabel;
    (node.getElementsByClassName("nbdime-header-remote")[0] as HTMLSpanElement).innerText = remoteLabel;

    return new Widget({node});
  }

  /**
   * Toggle whether to show or hide unchanged cells.
   *
   * This simply marks with a class, real work is done by CSS.
   */
  export
  function toggleShowUnchanged(root: Widget, show?: boolean) {
    let hiding = root.hasClass(HIDE_UNCHANGED_CLASS);
    if (show === undefined) {
      show = hiding;
    } else if (hiding !== show) {
      // Nothing to do
      return;
    }
    if (show) {
      root.removeClass(HIDE_UNCHANGED_CLASS);
    } else {
      markUnchangedRanges(root.node);
      root.addClass(HIDE_UNCHANGED_CLASS);
    }
    root.update();
  }


  /**
   * Gets the chunk element of an added/removed cell, or the cell element for others
   * @param cellElement
   */
  function getChunkElement(cellElement: Element): Element {
    if (!cellElement.parentElement || !cellElement.parentElement.parentElement) {
      return cellElement;
    }
    let chunkCandidate = cellElement.parentElement.parentElement;
    if (chunkCandidate.classList.contains(CHUNK_PANEL_CLASS)) {
      return chunkCandidate;
    }
    return cellElement;
  }


  /**
   * Marks certain cells with
   */
  export
  function markUnchangedRanges(root: HTMLElement) {
    let children = root.querySelectorAll(`.${CELLDIFF_CLASS}`);
    let rangeStart = -1;
    for (let i=0; i < children.length; ++i) {
      let child = children[i];
      if (!child.classList.contains(UNCHANGED_DIFF_CLASS)) {
        // Visible
        if (rangeStart !== -1) {
          // Previous was hidden
          let N = i - rangeStart;
          getChunkElement(child).setAttribute('data-nbdime-NCellsHiddenBefore', N.toString());
          rangeStart = -1;
        }
      } else if (rangeStart === -1) {
        rangeStart = i;
      }
    }
    if (rangeStart !== -1) {
      // Last element was part of a hidden range, need to mark
      // the last cell that will be visible.
      let N = children.length - rangeStart;
      if (rangeStart === 0) {
        // All elements were hidden, nothing to mark
        // Add info on root instead
        let tag = root.querySelector('.jp-Notebook-diff') || root;
        tag.setAttribute('data-nbdime-AllCellsHidden', N.toString());
        return;
      }
      let lastVisible = children[rangeStart - 1];
      getChunkElement(lastVisible).setAttribute('data-nbdime-NCellsHiddenAfter', N.toString());
    }
  }
}
