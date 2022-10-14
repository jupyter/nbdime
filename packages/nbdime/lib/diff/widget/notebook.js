// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';
Object.defineProperty(exports, "__esModule", { value: true });
exports.NotebookDiffWidget = void 0;
const widgets_1 = require("@lumino/widgets");
const cell_1 = require("./cell");
const common_1 = require("./common");
const metadata_1 = require("./metadata");
const NBDIFF_CLASS = 'jp-Notebook-diff';
/**
 * NotebookDiffWidget
 */
class NotebookDiffWidget extends widgets_1.Panel {
    constructor(model, rendermime) {
        super();
        this._model = model;
        this._rendermime = rendermime;
        this.addClass(NBDIFF_CLASS);
    }
    /**
     * Start adding sub-widgets.
     *
     * Separated from constructor to allow 'live' adding of widgets
     */
    init() {
        let model = this._model;
        let rendermime = this._rendermime;
        let work = Promise.resolve();
        work = work.then(() => {
            if (model.metadata) {
               this.addMetadata(model.metadata)
            }
        });
        for (let chunk of model.chunkedCells) {
            work = work.then(() => {
                return new Promise(resolve => {
                    this.addChunks(chunk);
                    // This limits us to drawing 60 cells per second, which shouldn't
                    // be a problem...
                    requestAnimationFrame(() => {
                        resolve();
                    });
                });
            });
        }
        return work;
    }

    /**
     * Get the model for the widget.
     *
     * #### Notes
     * This is a read-only property.
     */
    get model() {
        return this._model;
    }

    addChunks(chunk) {
        if (chunk.length === 1 && !(chunk[0].added || chunk[0].deleted)) {
            this.addWidget(this.addCellWidget(chunk[0]));
        }
        else {
            addChunkPanel(chunk)
        }
    }

    addChunkPanel(chunk) {
        let chunkPanel = new widgets_1.Panel();
        chunkPanel.addClass(common_1.CHUNK_PANEL_CLASS);
        let addedPanel = new widgets_1.Panel();
        addedPanel.addClass(common_1.ADDED_CHUNK_PANEL_CLASS);
        let removedPanel = new widgets_1.Panel();
        removedPanel.addClass(common_1.REMOVED_CHUNK_PANEL_CLASS);
        for (let cell of chunk) {
            let target = cell.deleted ? removedPanel : addedPanel;
            target.addWidget(this.addCellWidget(cell));
        }
        chunkPanel.addWidget(addedPanel);
        chunkPanel.addWidget(removedPanel);
        this.addWidget(chunkPanel);
    }

    addCellWidget(chunk) {
        return new cell_1.CellDiffWidget(chunk, this._rendermime, this._model.mimetype)
    }

    addMetadata(metadata) {
         this.addWidget(new metadata_1.MetadataDiffWidget(metadata));
    }
}
exports.NotebookDiffWidget = NotebookDiffWidget;
//# sourceMappingURL=notebook.js.map
