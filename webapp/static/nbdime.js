"use strict";

(function(nbdime) {

    // Note to new readers: if some code here looks weird,
    // my excuse is that I've been learning the quirks
    // of javascript/dom/css while writing this.
    // Please make pull requests and educate me!


    // from the nbdime diff format:
    // Valid values for the action field in diff entries
    var PATCH = "!";
    var INSERT = "+";
    var DELETE = "-";
    var REPLACE = ":";
    var SEQINSERT = "++";
    var SEQDELETE = "--";


    function convert_merge_data(data) {
        // FIXME: Convert data from server same as convert_diff_data
        var celldata = [
            ["cell0\nsame", "cell0\nsame", "cell0\nsame"],    // All same
            ["cell1\nlocal", "cell1\nbase", "cell1\nremote"], // All differ
            [null, "cell2\nbase", "cell2\nremote"],           // Local removed, remote modified
            ["cell3\nlocal", "cell3\nbase", null]             // Local modified, remote removed
        ];
        return celldata;
    }

    function convert_diff_data(data) {
        var b = data.base;
        var d = data.diff;

        // This is a temporary data conversion from the nbdime diff format
        // to the simplified format used while mocking up the web interface
        var celldata = [];

        var bcells = b.cells;
        var dcells = d.cells || [];
        var consumed = 0;
        for (var i=0; i<dcells.length; ++i) {
            var e = dcells[i];
            // nbdime diff format:
            var action = e[0];
            var index = e[1];

            // Add cells not mentioned in diff
            for (var j=consumed; j<index; ++j) {
                celldata.push([bcells[j], bcells[j]]);
            }

            if (action == SEQINSERT) {
                // Add inserted cells
                var newcells = e[2];
                for (var j=0; j<newcells.length; ++j) {
                    celldata.push([null, newcells[j]]);
                }
            } else if (action == SEQDELETE) {
                // Add deleted cells
                var num_deleted = e[2];
                for (var j=0; j<num_deleted; ++j) {
                    celldata.push([bcells[consumed+j], null]);
                }
                consumed += num_deleted;
            } else if (action == PATCH) {
                // Add modified cell
                var celldiff = e[2];
                celldata.push([bcells[consumed], celldiff]); // FIXME: This is the diff, not the cell
                consumed++;
            } else {
                throw "Invalid diff action.";
            }
        }
        // Add cells at end not mentioned in diff
        for (var j=consumed; j<bcells.length; ++j) {
            celldata.push([bcells[j], bcells[j]]);
        }

        return celldata;
    }

    /* Make a post request passing a json argument and receiving a json result. */
    function request_json(url, argument, callback, onError) {
        var xhttp = new XMLHttpRequest();
        xhttp.onreadystatechange = function() {
            if (xhttp.readyState == 4) {
                if (xhttp.status == 200) {
                    var result = JSON.parse(xhttp.responseText);
                    callback(result);
                } else {
                    onError();
                }
            }
        };
        xhttp.open("POST", url, true)
        xhttp.setRequestHeader("Content-type", "application/json");
        xhttp.send(JSON.stringify(argument));
    }


    function request_diff(base, remote) {
        request_json("/api/diff",
                     {base:base, remote:remote},
                     on_diff_request_completed,
                     on_diff_request_failed);
    }

    function on_diff_request_completed(data) {
        nbdime.init_diff(data);
    }

    function on_diff_request_failed() {
        console.log("Diff request failed.");
    }


    function request_merge(base, local, remote) {
        request_json("/api/merge",
                     {base:base, local:local, remote:remote},
                     on_merge_request_completed,
                     on_merge_request_failed);
    }

    function on_merge_request_completed(data) {
        nbdime.init_merge(data);
    }

    function on_merge_request_failed() {
        console.log("Merge request failed.");
    }


    function request_store_merge(merged) {
        request_json("/api/storemerge",
                     {merged:merged},
                     on_store_merge_request_completed,
                     on_store_merge_request_failed);
    }

    function on_store_merge_request_completed(data) {
        console.log("Store merge request:", data);
    }

    function on_merge_request_failed() {
        console.log("Store merge request failed.");
    }


    // TODO: Make a class to hold state instead of using globals.

    // Private variable holding the root element nbdime-root after
    // nbdime.init_diff() or nbdime.init_merge() have been called:
    // (are there better ways to do this?)
    var root;

    // List of all CodeMirror editor instances.
    // TODO: Store editors in a more accessible way.
    var editors = [];


    // TODO: Make this configurable
    var mode = "text/python";


    // Default arguments for codemirror instances
    function cm_args() {
        return {
            lineNumbers: true,
            indentUnit: 4,
            mode: mode
        };
    }


    // Default arguments for mergeview instances
    function mv_args() {
        return {
            lineNumbers: true,
            collapseIdentical: false,
            showDifferences: true,
            allowEditingOriginals: true,
            mode: mode
        };
    }


    function isString(s) {
        return typeof(s) === "string" || s instanceof String;
    }


    function add_editor(editor) {
        editors.push(editor);
    }


    // This just shows how to get content from editors.
    // Still missing: mapping editors to notebook cells
    // and recreating a full notebook.
    function extract_notebook() {
        var lines;
        var e;
        for (var i=0; i<editors.length; i++) {
            e = editors[i];
            lines = e.getDoc().getValue();
            console.log(lines);
        }
    }


    // Shorthand for creating element with children
    function elt(name, children, cls) {
        var node = document.createElement(name);
        if (cls) {
            if (cls !== null) {
                node.setAttribute("class", cls);
            }
        }
        if (children) {
            for (var i=0; i<children.length; i++) {
                var c = children[i];
                if (isString(c)) {
                    c = document.createTextNode(c);
                }
                node.appendChild(c);
            }
        }
        return node;
    }


    var model = {
        root: { // div class nbdime-root
            cells: { // ul class nbdime-cells
                cellrow: [ // il containing ul with class nbdime-cellrow
                    // cell with classes:
                    // nbdime-cell
                    // nbmerge-cell | nbdiff-cell
                    // nbmerge-cell-* | nbdiff-cell-*
                    ]
            }
        }
    };
    
    
    // This is the list of all cells
    function elt_diff_cells(rows) {
        return elt("ul", rows, "nbdime-cells"); // nbdiff-cells
    }


    function elt_merge_cells(rows) {
        return elt("ul", rows, "nbdime-cells"); // nbmerge-cells
    }


    // This is a row aligning conflicting cells
    function elt_cellrow(cells) {
        return elt("li", cells, null);
    }


    // This is the headers row of the cells list
    function elt_cell_headers(titles, cls) {
        var cells = [];
        for (var i=0; i<titles.length; i++) {
            cells.push(elt("span", [titles[i]], cls));
        }
        return elt_cellrow(cells);
    }


    // This is used for any single cell of various classes
    function elt_cell(cls) {
        return elt("span", [], "nbdime-cell " + cls);
    }


    function elt_diff_row(local, remote) {
        if (local === null || remote === null) {
            // Cell has been deleted or added, show on the left or right side

            // Create added cell with editor
            var ca = elt_cell("nbdiff-cell-added");
            var args = mv_args();
            args.value = remote === null ? local: remote;
            var editor = new CodeMirror(ca, args);
            add_editor(editor);

            // Create deleted cell
            var cd = elt_cell("nbdiff-cell-deleted");
            cd.appendChild(document.createTextNode("DELETED"));

            // Order cells depending on which side was deleted or added
            return elt_cellrow(remote === null ? [ca, cd]: [cd, ca]);
        } else if (local === remote) {
            // Cells are equal

            // Creating only one copy of the cell,
            //  but we can also add two equal cells with class nbdiff-cell-equal
            // if that's deemed more user friendly
            var c = elt_cell("nbdiff-cell-equal-content");
            var args = cm_args();
            args.value = local;
            var editor = new CodeMirror(c, args);
            add_editor(editor);

            var cl = elt_cell("nbdiff-cell-equal-left");
            var cr = elt_cell("nbdiff-cell-equal-right");
            return elt_cellrow([cl, c, cr]);
        } else {
            // Cells are different, show diff view
            var c = elt_cell("nbdiff-cells-twoway");

            var args = mv_args();
            args.value = local;
            args.orig = remote;
            var editor = new CodeMirror.MergeView(c, args);
            //add_editor(editor);

            //var doc = editor.editor().getDoc();
            //var lines = doc.getValue();
            //editor.editor().on(...);

            return elt_cellrow([c]);
        }
    }


    function elt_merge_row_unchanged(base) {
        var c = elt_cell("nbmerge-cell-equal-singular");
        var args = cm_args();
        args.value = base;
        var editor = new CodeMirror(c, args);
        add_editor(editor);

        return elt_cellrow([c]);
    }


    function elt_merge_row_deleted(local, base, remote) {
        // Create deleted cell (one side deleted)
        var cdel = elt_cell("nbmerge-cell-deleted");
        cdel.appendChild(document.createTextNode("DELETED"));

        // Create twoway diff cell
        var cdiff = elt_cell("nbmerge-cell-twoway");
        var args = mv_args();
        if (1) {
            args.origLeft = local;
            args.value = base;
            args.origRight = remote;
        } else {
            // Possible workaround for minor bugs in codemirror MergeView when passing origRight: null
            if (local === null) {
                args.value = base;
                args.orig = remote;
            } else {
                args.value = local;
                args.orig = base;
            }
        }
        var editor = new CodeMirror.MergeView(cdiff, args);
        add_editor(editor);

        // Put row together
        return elt_cellrow(remote === null ? [cdiff, cdel]: [cdel, cdiff]);
    }


    function elt_merge_row_full(local, base, remote) {
        var mergecell = elt_cell("nbmerge-cell-threeway");
        var args = mv_args();
        args.origLeft = local;
        args.value = base;
        args.origRight = remote;
        var editor = new CodeMirror.MergeView(mergecell, args);
        add_editor(editor);

        return elt_cellrow([mergecell]);
    }


    function elt_merge_row(local, base, remote) {
        if (local === null || remote === null) {
            // This shouldn't happen with valid celldata
            if (local === null && remote === null)
                throw "Not expecting cells deleted on both sides here.";
            // Cell deleted on one side and modified on the other
            return elt_merge_row_deleted(local, base, remote);
        } else if (local !== base || remote !== base) {
            // Cell modified on both sides
            // (if it was only modified on one side,
            // that has already been merged into base)
            return elt_merge_row_full(local, base, remote);
        } else {
            // Cell not involved in conflict
            return elt_merge_row_unchanged(base);
        }
    }


    function elt_diff_buttons() {
        var b0 = elt("button", ["Extract editor contents"], null);
        b0.setAttribute("type", "button");
        b0.onclick = extract_notebook;
        return elt("div", [b0], null);
    }


    // The main page generation script for nbdiff
    function elt_nbdiff_view(celldata) {
        // For each cell, generate an aligned row depending on conflict status:
        var rows = [elt_cell_headers(["Base", "Remote"], "nbdiff-cell-header")];
        for (var i=0; i<celldata.length; ++i) {
            // FIXME: Render cells properly, this just dumps cell json in editor
            var data = celldata[i];
            var base = data[0] == null ? null: JSON.stringify(data[0]);
            var remote = data[1] == null ? null: JSON.stringify(data[1]);
            rows.push(elt_diff_row(base, remote));
        }
        rows.push(elt_diff_buttons());  // This is nothing interesting yet
        return elt_diff_cells(rows);
    }


    // The main page generation script for nbmerge
    function elt_nbmerge_view(celldata) {
        // For each cell, generate an aligned row depending on conflict status:
        var rows = [elt_cell_headers(["Local", "Base", "Remote"], "nbmerge-cell-header")];
        for (var i=0; i<celldata.length; ++i) {
            // FIXME: Render cells properly, this just dumps cell json in editor
            var data = celldata[i];
            var base = data[0] == null ? null: JSON.stringify(data[0]);
            var local = data[1] == null ? null: JSON.stringify(data[1]);
            var remote = data[2] == null ? null: JSON.stringify(data[2]);
            rows.push(elt_merge_row(base, local, remote));
        }
        return elt_merge_cells(rows);
    }


    // To make nbdime more reusable, it's possible to take the root element
    // as argument to a constructor instead like CodeMirror does.
    function get_cleared_root() {
        // Find root div element to place everything inside
        var root = document.getElementById("nbdime-root");
        if (root === null) {
            throw "Found no div element with id nbdime-root in document.";
        }
        // Clear eventual html from root element
        root.innerHTML = "";
        // Clear list of CodeMirror editors
        editors = [];
        return root;
    }


    // This seems to be necessary to let the codemirror
    // editors resize to fit their place on the page
    function refresh_editors() {
        for (var i=0; i<editors.length; i++) {
            editors[i].refresh();
        }
    }


    // Initialization. Intended usage is to set body.onload=nbdime.init_diff() in parent document.
    nbdime.init_diff = function(data) {
        var celldata = convert_diff_data(data);
        var view = elt_nbdiff_view(celldata);
        var root = get_cleared_root();
        root.appendChild(view);
        refresh_editors();
    }


    // Initialization. Intended usage is to set body.onload=nbdime.init_merge() in parent document.
    nbdime.init_merge = function(data) {
        var celldata = convert_merge_data(data);
        var view = elt_nbmerge_view(celldata);
        var root = get_cleared_root();
        root.appendChild(view);
        refresh_editors();
    }


    /* Insert callbacks here for UI actions. */

    nbdime.on_diff = function() {
        var b = document.getElementById("merge-base").value;
        var r = document.getElementById("merge-remote").value;
        request_diff(b, r);
    }


    nbdime.on_merge = function() {
        var b = document.getElementById("merge-base").value;
        var l = document.getElementById("merge-local").value;
        var r = document.getElementById("merge-remote").value;
        request_merge(b, l, r);
    }


    nbdime.on_use_local = function() {
        alert("TODO: Add handler!");
    }


    nbdime.on_use_base = function() {
        alert("TODO: Add handler!");
    }


    nbdime.on_use_remote = function() {
        alert("TODO: Add handler!");
    }


    nbdime.on_use_none = function() {
        alert("TODO: Add handler!");
    }


    /* This function is called just after it's defined,
       passing the object window.nbdime or a new object as argument,
       simultaneously storing this new object on the window,
       with the result that nbdime above is in the global
       namespace of the page in this window: */
})(window.nbdime = window.nbdime || {});
