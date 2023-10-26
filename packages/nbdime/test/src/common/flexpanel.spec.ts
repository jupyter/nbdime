// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

import { Widget } from '@lumino/widgets';

import { FlexPanel } from '../../../src/upstreaming/flexpanel';

/**
 * Perform tests where a set of steps should give the same behavior
 * regardless of their order of execution.
 *
 * For example, for the operations A, B and C, this will run:
 *   ABC, ACB, BAC, BCA, CAB, CBA
 *
 * If beforeEach is not null/undefined if will be called before
 * each permutation, and similarly afterEach will be called after
 * each permutation.
 */
function combinatorialTest(
  description: string,
  steps:
    | ((done: jest.DoneCallback) => void)[]
    | { [key: string]: (done?: jest.DoneCallback) => void },
  beforeEach?: (done: jest.DoneCallback) => void,
  afterEach?: (done: jest.DoneCallback) => void,
) {
  let stepNames: string[];
  if (Array.isArray(steps)) {
    stepNames = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');
  } else {
    stepNames = Object.keys(steps);
    let stepArray: ((done?: jest.DoneCallback) => void)[] = [];
    for (let key of stepNames) {
      stepArray.push(steps[key]);
    }
    steps = stepArray;
  }
  function range(start: number, count: number): number[] {
    return Array.apply(0, Array(count)).map(function (
      element: unknown,
      index: number,
      array: unknown[],
    ) {
      return index + start;
    });
  }
  function combine(
    items: number | number[],
    combinations?: number[][],
    partial?: number[],
  ): number[][] {
    if (!Array.isArray(items)) {
      items = range(0, items);
    }
    if (!combinations) {
      combinations = [];
    }
    if (!partial) {
      partial = [];
    }
    if (items.length === 1) {
      let completed = partial.concat(items);
      combinations.push(completed);
    } else {
      for (let i = 0; i < items.length; i++) {
        let rest = items.slice();
        let current = partial.concat(rest.splice(i, 1)[0]);
        combine(rest, combinations, current);
      }
    }
    return combinations;
  }

  let permutations = combine(steps.length);
  let tSteps = steps; // Typings get confused
  for (let p of permutations) {
    let permStepNames: string[] = [];
    for (let i of p) {
      permStepNames.push(stepNames[i]);
    }
    let stepStr = permStepNames.join(', ');
    it(description + ' :: Permutation: ' + stepStr, done => {
      if (beforeEach) {
        beforeEach(done);
      }
      for (let i of p) {
        let step = tSteps[i];
        step(done);
      }
      if (afterEach) {
        afterEach(done);
      }
    });
  }
}

describe('upstreaming', () => {
  describe('FlexPanel', () => {
    it('should be initialized with no options', () => {
      let p = new FlexPanel();
      expect(p).not.toBe(null);
    });

    it('should add a class name to the flex panel', () => {
      let p = new FlexPanel();
      expect(p.hasClass('lm-FlexPanel')).toBe(true);
    });

    it('should add a class name to the flex panel children', () => {
      let p = new FlexPanel();
      p.addWidget(new Widget());
      p.addWidget(new Widget());
      p.addWidget(new Widget());
      for (const child of p.widgets) {
        expect(child.hasClass('lm-FlexPanel-child')).toBe(true);
      }
    });

    it('should remove child class name when removing a child widget', () => {
      let p = new FlexPanel();
      p.addWidget(new Widget());
      p.addWidget(new Widget());
      p.addWidget(new Widget());
      while (p.widgets.length > 0) {
        let child = p.widgets[0];
        child.parent = null!;
        expect(child.hasClass('lm-FlexPanel-child')).toBe(false);
      }
    });

    it('should set and get direction', () => {
      let p = new FlexPanel();
      // Check that it has a valid initial value
      p.direction = 'bottom-to-top';
      expect(p.direction).toBe('bottom-to-top');
    });

    it('should apply direction if attached after setting', () => {
      let p = new FlexPanel();
      p.direction = 'bottom-to-top';
      Widget.attach(p, document.body);
      expect(p.hasClass('lm-mod-bottom-to-top')).toBe(true);
    });

    it('should apply direction if attached before setting', () => {
      let p = new FlexPanel();
      Widget.attach(p, document.body);
      p.direction = 'bottom-to-top';
      expect(p.hasClass('lm-mod-bottom-to-top')).toBe(true);
    });

    it('should report isHorizontal/isVertical correctly', () => {
      let p = new FlexPanel();
      for (let v of ['top-to-bottom', 'bottom-to-top']) {
        p.direction = v as any;
        expect(p.layout.isHorizontal()).toBe(false);
        expect(p.layout.isVertical()).toBe(true);
      }
      for (let v of ['left-to-right', 'right-to-left']) {
        p.direction = v as any;
        expect(p.layout.isHorizontal()).toBe(true);
        expect(p.layout.isVertical()).toBe(false);
      }
    });

    it('should set and get minimumSpacing', () => {
      let p = new FlexPanel();
      // Check that it has a valid initial value
      p.minimumSpacing = 10;
      expect(p.minimumSpacing).toBe(10);
    });

    let p: FlexPanel;
    let child: Widget;

    combinatorialTest(
      'should set minimumSpacing irregardless of operation order',
      {
        addChild: () => {
          p.addWidget(child);
          p.addWidget(new Widget());
        },
        setValue: () => {
          p.minimumSpacing = 10;
        },
        attachParent: () => {
          Widget.attach(p, document.body);
        },
      },
      () => {
        p = new FlexPanel();
        child = new Widget();
      },
      done => {
        requestAnimationFrame(() => {
          try {
            expect(child.node.style.marginBottom).toBe('10px');
          } finally {
            p.close();
            p.dispose();
          }
          done();
        });
      },
    );

    it('should set and get wrap', () => {
      let p = new FlexPanel();
      // Check that it has a valid initial value
      p.wrap = true;
      expect(p.wrap).toBe(true);
    });

    it('should apply wrap if attached after setting', done => {
      let p = new FlexPanel();
      p.wrap = true;
      Widget.attach(p, document.body);
      requestAnimationFrame(() => {
        expect(p.node.style.flexWrap).toBe('wrap');
        p.dispose();
        done();
      });
    });

    it('should apply wrap if attached before setting', done => {
      let p = new FlexPanel();
      Widget.attach(p, document.body);
      p.wrap = true;
      requestAnimationFrame(() => {
        expect(p.node.style.flexWrap).toBe('wrap');
        p.dispose();
        done();
      });
    });

    it('should set and get justifyContent', () => {
      let p = new FlexPanel();
      expect(p.justifyContent).toBe(null);
      p.justifyContent = 'center';
      expect(p.justifyContent).toBe('center');
    });

    it('should apply justifyContent if attached after setting', done => {
      let p = new FlexPanel();
      p.justifyContent = 'center';
      Widget.attach(p, document.body);
      requestAnimationFrame(() => {
        expect(p.node.style.justifyContent).toBe('center');
        p.dispose();
        done();
      });
    });

    it('should apply justifyContent if attached before setting', done => {
      let p = new FlexPanel();
      Widget.attach(p, document.body);
      p.justifyContent = 'center';
      requestAnimationFrame(() => {
        expect(p.node.style.justifyContent).toBe('center');
        p.dispose();
        done();
      });
    });

    it('should set and get alignItems', () => {
      let p = new FlexPanel();
      expect(p.alignItems).toBe(null);
      p.alignItems = 'center';
      expect(p.alignItems).toBe('center');
    });

    it('should apply alignItems if attached after setting', done => {
      let p = new FlexPanel();
      p.alignItems = 'center';
      Widget.attach(p, document.body);
      requestAnimationFrame(() => {
        expect(p.node.style.alignItems).toBe('center');
        p.dispose();
        done();
      });
    });

    it('should apply alignItems if attached before setting', done => {
      let p = new FlexPanel();
      Widget.attach(p, document.body);
      p.alignItems = 'center';
      requestAnimationFrame(() => {
        expect(p.node.style.alignItems).toBe('center');
        p.dispose();
        done();
      });
    });

    it('should set and get alignContent', () => {
      let p = new FlexPanel();
      expect(p.alignContent).toBe(null);
      p.alignContent = 'center';
      expect(p.alignContent).toBe('center');
    });

    it('should apply alignContent if attached after setting', done => {
      let p = new FlexPanel();
      p.alignContent = 'center';
      Widget.attach(p, document.body);
      requestAnimationFrame(() => {
        expect(p.node.style.alignContent).toBe('center');
        p.dispose();
        done();
      });
    });

    it('should apply alignContent if attached before setting', done => {
      let p = new FlexPanel();
      Widget.attach(p, document.body);
      p.alignContent = 'center';
      requestAnimationFrame(() => {
        expect(p.node.style.alignContent).toBe('center');
        p.dispose();
        done();
      });
    });

    it('should set and get stretchType', () => {
      let p = new FlexPanel();
      expect(p.stretchType).toBe(null);
      p.stretchType = 'both';
      expect(p.stretchType).toBe('both');
    });

    combinatorialTest(
      'should set stretchType irregardless of operation order',
      {
        addChild: () => {
          p.addWidget(child);
        },
        setValue: () => {
          p.stretchType = 'both';
        },
        attachParent: () => {
          Widget.attach(p, document.body);
        },
      },
      () => {
        p = new FlexPanel();
        child = new Widget();
      },
      done => {
        requestAnimationFrame(() => {
          try {
            expect(child.node.style.flexGrow).toBe('1');
            expect(child.node.style.flexShrink).toBe('1');
          } finally {
            p.close();
            p.dispose();
          }
          done();
        });
      },
    );

    it('should set and get evenSizes', () => {
      let p = new FlexPanel();
      expect(p.evenSizes).toBe(false);
      p.evenSizes = true;
      expect(p.evenSizes).toBe(true);
    });

    combinatorialTest(
      'should apply evenSizes regardless of operations order',
      {
        addChild: () => {
          p.addWidget(child);
        },
        setValue: () => {
          p.evenSizes = true;
        },
        attachParent: () => {
          Widget.attach(p, document.body);
        },
      },
      () => {
        p = new FlexPanel();
        child = new Widget();
      },
      done => {
        requestAnimationFrame(() => {
          try {
            expect(child.node.style.flexBasis).toBe('0px');
            expect(child.node.style.flexGrow).toBe('1');
            expect(child.node.style.flexShrink).toBe('');
          } finally {
            p.close();
            p.dispose();
          }
          done();
        });
      },
    );
  });
});
