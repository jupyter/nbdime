// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';


import {
  IModel, CellDiffModel
} from '../diff/model';

import {
  DecisionPath
} from './decisions';

import {
  NotebookMergeModel, CellMergeModel
} from './model';


export
function getRootModel(model: IModel): IModel {
  while (model.parent !== null){
    model = model.parent;
  }
  return model;
}


export
function getPathForNewDecision(model: IModel): [DecisionPath, DecisionPath | null] {
  let parent = model.parent;
  if (parent === null) {
    // We are a root level model
    return [[], null];
  }
  if (parent instanceof NotebookMergeModel) {
    if (model === parent.metadata) {
      return [['metadata'], null];
    }
    let cm = model as CellMergeModel;
    if (cm.base === null) {
      // Inserted cell
      return [['cells'], []];
    } else {
      let idx = parent.base.cells.indexOf(cm.base);
      if (idx === -1) {
        throw new Error('Invalid model');
      }
      return [['cells', idx], null];
    }
  }
  let parentPath = getPathForNewDecision(parent);
  // If parent is inserted cell, this will pick subpath:
  let subpath = parentPath[1] || parentPath[0];
  if (parent instanceof CellDiffModel) {
    if (model === parent.source) {
      subpath.push('source');
    } else if (model === parent.metadata) {
      subpath.push('metadata');
    }
    return parentPath;
    // Do not support editing on outputs, so excluded
  } else if (parent instanceof CellMergeModel) {
    if (model === parent.merged.source) {
      subpath.push('source');
    } else if (model === parent.merged.metadata) {
      subpath.push('metadata');
    }
    return parentPath;
    // Do not support editing on outputs, so excluded
  }
  throw new Error('Could not find path for model');
}
