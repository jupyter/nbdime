// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import {
  ISanitizer
} from '@jupyterlab/apputils';

import {
  URLExt
} from '@jupyterlab/coreutils';

import {
  IRenderMime, defaultRendererFactories, markdownRendererFactory,
} from '@jupyterlab/rendermime';

import {
  UNCHANGED_IMAGE
} from './res';


export
class MarkdownImageResolver implements IRenderMime.IResolver {
  constructor(public innerResolver: IRenderMime.IResolver | null) {
  }

  resolveUrl(url: string): Promise<string> {
    // Do nothing here
    if (!this.innerResolver) {
      return Promise.resolve(url);
    }
    return this.innerResolver.resolveUrl(url);
  }

  /**
   * Get the download url of a given absolute server path.
   */
  getDownloadUrl(path: string): Promise<string>{
    if (URLExt.isLocal(path)) {
      // Check if it is an image, if so, replace it with our own placeholder
      if (path.match(/.*\.(png|apng|svg|jpeg|jpg|bmp|ico|gif|xbm)$/i)) {
        return Promise.resolve(UNCHANGED_IMAGE);
      }
    }
    if (!this.innerResolver) {
      return Promise.resolve(path);
    }
    return this.innerResolver.getDownloadUrl(path);
  }
}


class NbdimeMarkdownFactory implements IRenderMime.IRendererFactory {
  readonly safe = markdownRendererFactory.safe;
  readonly mimeTypes = markdownRendererFactory.mimeTypes;

  createRenderer(options: IRenderMime.IRendererOptions): IRenderMime.IRenderer {
    options.resolver = new MarkdownImageResolver(options.resolver);
    return markdownRendererFactory.createRenderer(options);
  }
}


let factories: IRenderMime.IRendererFactory[] = [];
for (let f of defaultRendererFactories) {
  if (f === markdownRendererFactory) {
    factories.push(new NbdimeMarkdownFactory());
  } else {
    factories.push(f);
  }
}

export
const rendererFactories: ReadonlyArray<IRenderMime.IRendererFactory> = factories;

