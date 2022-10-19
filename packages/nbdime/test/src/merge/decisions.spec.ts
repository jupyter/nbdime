// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

import * as decisions from "../../../src/merge/decisions";

import {
  opAdd,
  opRemove,
  opAddRange,
  opRemoveRange,
  opPatch,
  IDiffEntry,
  IDiffPatch,
  DiffCollection,
} from "../../../src/diff/diffentries";

import { arraysEqual } from "../../../src/common/util";

function isDiffEmpty(diff: IDiffEntry[] | null): boolean {
  if (diff === null || diff.length === 0) {
    return true;
  }
  for (let e of diff) {
    if (e.op !== "patch") {
      return false;
    }
    if (!isDiffEmpty(e.diff)) {
      return false;
    }
  }
  return true;
}

describe("merge", () => {
  describe("decisions", () => {
    describe("MergeDecision class", () => {
      let jsonStructure: decisions.IMergeDecision = {
        action: "custom",
        local_diff: [opAdd("two", 22)],
        remote_diff: [opAdd("two", 33)],
        custom_diff: [opAdd("two", 55)],
        conflict: true,
        common_path: ["a", 0, "32", "foo", "bar"],
      };

      it("should initialize by full JSON structure", () => {
        let value = new decisions.MergeDecision(jsonStructure);
        expect(value.action).toEqual(jsonStructure.action);
        expect(value.localDiff).toEqual(jsonStructure.local_diff);
        expect(value.remoteDiff).toEqual(jsonStructure.remote_diff);
        expect(value.customDiff).toEqual(jsonStructure.custom_diff);
        expect(value.conflict).toEqual(jsonStructure.conflict);
        expect(value.absolutePath).toEqual(jsonStructure.common_path);
      });

      it("should serialize out a JSON structure", () => {
        let d = new decisions.MergeDecision(
          jsonStructure.common_path!,
          jsonStructure.local_diff,
          jsonStructure.remote_diff,
          jsonStructure.action as decisions.Action,
          jsonStructure.conflict,
          jsonStructure.custom_diff
        );
        let value = d.serialize();
        expect(value).toEqual(jsonStructure);
      });

      it("should recreate a JSON structure from constructor/serialize", () => {
        let value = new decisions.MergeDecision(jsonStructure).serialize();
        expect(value).toEqual(jsonStructure);
      });

      it("should initialize to defaults by partial JSON structure", () => {
        // Check everything in one go with empty structure:
        let s: decisions.IMergeDecision = {};
        let value = new decisions.MergeDecision(s);
        expect(value.action).toEqual("base");
        expect(value.localDiff).toEqual(null);
        expect(value.remoteDiff).toEqual(null);
        expect(value.customDiff).toEqual(null);
        expect(value.conflict).toEqual(false);
        expect(value.absolutePath).toEqual([]);
      });

      it("should initialize by copy constructor", () => {
        // Check everything in one go with empty structure:
        let initial = new decisions.MergeDecision(jsonStructure);
        let value = new decisions.MergeDecision(initial);
        expect(value.action).toEqual(jsonStructure.action);
        expect(value.localDiff).toEqual(jsonStructure.local_diff);
        expect(value.remoteDiff).toEqual(jsonStructure.remote_diff);
        expect(value.customDiff).toEqual(jsonStructure.custom_diff);
        expect(value.conflict).toEqual(jsonStructure.conflict);
        expect(value.absolutePath).toEqual(jsonStructure.common_path);
      });

      it("should slice localPath to level", () => {
        let value = new decisions.MergeDecision(jsonStructure);
        expect(value.localPath).toEqual(jsonStructure.common_path);

        for (let i = 0; i <= jsonStructure.common_path!.length; ++i) {
          value.level = i;
          expect(value.localPath).toEqual(jsonStructure.common_path!.slice(i));
        }
      });

      it("should be able to push a path", () => {
        let value = new decisions.MergeDecision(jsonStructure);

        value.pushPath("test");
        expect(value.absolutePath).toEqual([
          "a",
          0,
          "32",
          "foo",
          "bar",
          "test",
        ]);
      });

      it("should be able to set absolute path", () => {
        let value = new decisions.MergeDecision(jsonStructure);
        let path = ["a", 5];
        value.absolutePath = path;
        expect(value.absolutePath).toEqual(path);
        expect(value.localPath).toEqual(path);
      });

      it("should be able to get diffs", () => {
        let value = new decisions.MergeDecision(jsonStructure);

        value.customDiff = null;

        expect(value.diffs).toEqual([
          jsonStructure.local_diff,
          jsonStructure.remote_diff,
        ]);
      });

      it("should be able to set diffs", () => {
        let value = new decisions.MergeDecision(jsonStructure);

        value.diffs = [jsonStructure.remote_diff!, jsonStructure.local_diff!];

        expect(value.localDiff).toEqual(jsonStructure.remote_diff);
        expect(value.remoteDiff).toEqual(jsonStructure.local_diff);

        value.diffs = [
          jsonStructure.local_diff!,
          jsonStructure.remote_diff!,
          null,
        ];

        expect(value.localDiff).toEqual(jsonStructure.local_diff);
        expect(value.remoteDiff).toEqual(jsonStructure.remote_diff);
        expect(value.customDiff).toEqual(null);
      });

      it("should have diffs include custom diff if set", () => {
        let value = new decisions.MergeDecision(jsonStructure);

        expect(value.diffs).toEqual([
          jsonStructure.local_diff,
          jsonStructure.remote_diff,
          jsonStructure.custom_diff,
        ]);
      });
    });

    describe("popPath", () => {
      it("should always pop patch paths if only passed one diff", () => {
        let diffs: IDiffEntry[][] = [
          [opPatch("a", [opPatch(0, [opPatch("foo", [opAdd("two", "bar")])])])],
        ];
        let value = decisions.popPath(diffs)!;
        expect(value.key).toBe("a");
        expect(value.diffs.length).toBe(1);
        expect(value.diffs[0]).toEqual((diffs[0][0] as IDiffPatch).diff);

        diffs = [(diffs[0][0] as IDiffPatch).diff!];
        value = decisions.popPath(diffs)!;
        expect(value.key).toBe(0);
        expect(value.diffs.length).toBe(1);
        expect(value.diffs[0]).toEqual((diffs[0][0] as IDiffPatch).diff);

        diffs = [(diffs[0][0] as IDiffPatch).diff!];
        value = decisions.popPath(diffs)!;
        expect(value.key).toBe("foo");
        expect(value.diffs.length).toBe(1);
        expect(value.diffs[0]).toEqual((diffs[0][0] as IDiffPatch).diff);
      });

      it("should pop shared patch paths", () => {
        let diffs: IDiffEntry[][] = [
          [opPatch("a", [opPatch(0, [opAdd("three", "bar")])])],
          [opPatch("a", [opPatch(0, [opAdd("two", "whizz")])])],
        ];
        let value = decisions.popPath(diffs)!;
        expect(value.key).toBe("a");
        expect(value.diffs.length).toBe(2);
        expect(value.diffs[0]).toEqual((diffs[0][0] as IDiffPatch).diff);
        expect(value.diffs[1]).toEqual((diffs[1][0] as IDiffPatch).diff);

        diffs = [
          (diffs[0][0] as IDiffPatch).diff!,
          (diffs[1][0] as IDiffPatch).diff!,
        ];
        value = decisions.popPath(diffs)!;
        expect(value.key).toBe(0);
        expect(value.diffs.length).toBe(2);
        expect(value.diffs[0]).toEqual((diffs[0][0] as IDiffPatch).diff);
        expect(value.diffs[1]).toEqual((diffs[1][0] as IDiffPatch).diff);
      });

      it("should pop patch path if one entry is null", () => {
        let diffs: DiffCollection = [
          [opPatch("a", [opPatch(0, [opAdd("three", "bar")])])],
          null,
        ];
        let value = decisions.popPath(diffs)!;
        expect(value.key).toBe("a");
        expect(value.diffs.length).toBe(2);
        expect(value.diffs[0]).toEqual((diffs[0]![0] as IDiffPatch).diff);
        expect(value.diffs[1]).toEqual(null);

        // Check there is no preference for order:
        diffs = [null, [opPatch("a", [opPatch(0, [opAdd("three", "bar")])])]];
        value = decisions.popPath(diffs)!;
        expect(value.key).toBe("a");
        expect(value.diffs.length).toBe(2);
        expect(value.diffs[0]).toEqual(null);
        expect(value.diffs[1]).toEqual((diffs[1]![0] as IDiffPatch).diff);
      });

      it("should NOT pop patch path if only one side has patch", () => {
        let diffs: IDiffEntry[][] = [
          [opPatch("a", [opPatch(0, [opAdd("three", "bar")])])],
          [opAdd("b", "bar")],
        ];
        let value = decisions.popPath(diffs);
        expect(value).toBe(null);
      });

      it("should NOT pop patch path if only one side has multiple entries", () => {
        let diffs: IDiffEntry[][] = [
          [opPatch("a", [opPatch(0, [opAdd("three", "bar")])])],
          [
            opPatch("a", [opPatch(0, [opAdd("three", "bar")])]),
            opAdd("b", "bar"),
          ],
        ];
        let value = decisions.popPath(diffs);
        expect(value).toBe(null);

        diffs = [
          [opPatch("a", [opPatch(0, [opAdd("three", "bar")])])],
          [
            opAdd("b", "bar"),
            opPatch("a", [opPatch(0, [opAdd("three", "bar")])]),
          ],
        ];
        value = decisions.popPath(diffs);
        expect(value).toBe(null);
      });

      it("should NOT pop path if both sides has multiple entries", () => {
        let diffs: IDiffEntry[][] = [
          [
            opPatch("a", [opPatch(0, [opAdd("three", "bar")])]),
            opAdd("b", "bar"),
          ],
          [
            opPatch("a", [opPatch(0, [opAdd("three", "bar")])]),
            opAdd("b", "bar"),
          ],
        ];
        let value = decisions.popPath(diffs);
        expect(value).toBe(null);

        diffs = [
          [
            opAdd("b", "bar"),
            opPatch("a", [opPatch(0, [opAdd("three", "bar")])]),
          ],
          [
            opAdd("b", "bar"),
            opPatch("a", [opPatch(0, [opAdd("three", "bar")])]),
          ],
        ];
        value = decisions.popPath(diffs);
        expect(value).toBe(null);
      });

      it("should return null on empty input", () => {
        expect(decisions.popPath([])).toBe(null);
        expect(decisions.popPath([[], []])).toBe(null);
        expect(decisions.popPath([null, null])).toBe(null);
      });

      it("should only pop patch path if inner diffs have a length of 1, or if popInner is true", () => {
        let diffs: IDiffEntry[][] = [
          [opPatch(0, [opAdd("three", "bar"), opAdd("two", "bar")])],
          [opPatch(0, [opAdd("three", "bar"), opAdd("one", "bar")])],
        ];
        let value = decisions.popPath(diffs);
        expect(value).toBe(null);

        value = decisions.popPath(diffs, true)!;
        expect(value).not.toBe(null);
        expect(value.key).toBe(0);
        expect(value.diffs[0]!.length).toBe(2);
        expect(value.diffs[1]!.length).toBe(2);

        diffs = [
          [opPatch(0, [opAdd("three", "bar")])],
          [opPatch(0, [opAdd("three", "bar"), opAdd("one", "bar")])],
        ];
        value = decisions.popPath(diffs);
        expect(value).toBe(null);

        value = decisions.popPath(diffs, true)!;
        expect(value).not.toBe(null);
        expect(value.key).toBe(0);
        expect(value.diffs[0]!.length).toBe(1);
        expect(value.diffs[1]!.length).toBe(2);

        diffs = [
          [opPatch(0, [opAdd("three", "bar"), opAdd("two", "bar")])],
          [opPatch(0, [opAdd("three", "bar")])],
        ];
        value = decisions.popPath(diffs);
        expect(value).toBe(null);

        value = decisions.popPath(diffs, true)!;
        expect(value).not.toBe(null);
        expect(value.key).toBe(0);
        expect(value.diffs[0]!.length).toBe(2);
        expect(value.diffs[1]!.length).toBe(1);
      });
    });

    describe("resolveCommonPaths", () => {
      it("should move patch ops to common path", () => {
        let decs = [
          new decisions.MergeDecision(
            [],
            [opPatch("a", [opPatch(0, [opPatch("foo", null)])])],
            [opPatch("a", [opPatch(0, [opRemove("foo")])])]
          ),
          new decisions.MergeDecision(
            [],
            [opPatch(33, [opPatch(0, [opPatch("foo", null)])])],
            [opPatch(33, [opPatch(0, null)])]
          ),
        ];

        decisions.resolveCommonPaths(decs);
        expect(decs.length).toBe(2);
        expect(decs[0].absolutePath).toEqual(["a", 0]);
        expect(decs[1].absolutePath).toEqual([33, 0, "foo"]);
      });
    });

    describe("pushPatchDecision", () => {
      let simpleDecision: decisions.IMergeDecision = {
        local_diff: [opAddRange(3, ["line 4\n"])],
        remote_diff: [opAddRange(3, ["alternative line 4\n"])],
        common_path: ["cells", 3, "source"],
      };

      it("should push a single level prefix", () => {
        let dec = new decisions.MergeDecision(simpleDecision);
        let value = decisions.pushPatchDecision(dec, ["source"]);
        expect(value.absolutePath).toEqual(["cells", 3]);
        expect(value.localDiff).toEqual([opPatch("source", dec.localDiff)]);
        expect(value.remoteDiff).toEqual([opPatch("source", dec.remoteDiff)]);
      });

      it("should push a multi-level prefix", () => {
        let dec = new decisions.MergeDecision(simpleDecision);
        let value = decisions.pushPatchDecision(dec, ["cells", 3, "source"]);
        expect(value.absolutePath).toEqual([]);
        expect(value.localDiff).toEqual([
          opPatch("cells", [opPatch(3, [opPatch("source", dec.localDiff)])]),
        ]);
        expect(value.remoteDiff).toEqual([
          opPatch("cells", [opPatch(3, [opPatch("source", dec.remoteDiff)])]),
        ]);
      });

      it("should only change path if diffs are missing", () => {
        let dec = new decisions.MergeDecision(simpleDecision);
        dec.localDiff = dec.remoteDiff = null;
        let value = decisions.pushPatchDecision(dec, ["cells", 3, "source"]);
        expect(value.absolutePath).toEqual([]);
        // Check that everything else is unchanged:
        dec.absolutePath = [];
        expect(value.serialize()).toEqual(dec.serialize());
      });

      it("should push a custom diff as well", () => {
        let dec = new decisions.MergeDecision(simpleDecision);
        dec.customDiff = dec.localDiff;
        dec.localDiff = dec.remoteDiff = null;
        let value = decisions.pushPatchDecision(dec, ["source"]);
        expect(value.absolutePath).toEqual(["cells", 3]);
        expect(value.customDiff).toEqual([opPatch("source", dec.customDiff)]);
      });

      it("should fail to push an invalid prefix", () => {
        let dec = new decisions.MergeDecision(simpleDecision);
        expect(() => {
          decisions.pushPatchDecision(dec, ["cells"]);
        }).toThrow(
          /Cannot push a patch that doesn\'t correspond to a key in the decision path!/
        );
      });

      it("should fail to push a prefix longer than path", () => {
        let dec = new decisions.MergeDecision(simpleDecision);
        expect(() => {
          decisions.pushPatchDecision(dec, ["/", "cells", 3, "source"]);
        }).toThrow(/Cannot remove key from empty decision path: /);
      });
    });

    describe("buildDiffs", () => {
      let base = {
        source: "line 1\nline 2\nline 3 is longer\n",
        metadata: {
          secret: "foo!",
        },
      };

      let simpleDecision: decisions.IMergeDecision = {
        local_diff: [opAddRange(3, ["line 4\n"])],
        remote_diff: [opAddRange(3, ["alternative line 4\n"])],
        common_path: ["source"],
      };

      it("should build a simple local diff irregardless of action", () => {
        let dec = new decisions.MergeDecision(simpleDecision);
        for (let a of [
          "base",
          "local",
          "remote",
          "clear",
          "local_then_remote",
        ]) {
          dec.action = a as any;
          let value = decisions.buildDiffs(base, [dec], "local");
          expect(value).toEqual([opPatch("source", dec.localDiff)]);
        }
      });

      it("should build a simple remote diff irregardless of action", () => {
        let dec = new decisions.MergeDecision(simpleDecision);
        for (let a of [
          "base",
          "local",
          "remote",
          "clear",
          "local_then_remote",
        ]) {
          dec.action = a as any;
          let value = decisions.buildDiffs(base, [dec], "remote");
          expect(value).toEqual([opPatch("source", dec.remoteDiff)]);
        }
      });

      it("should build a simple merged diff for local decision", () => {
        let dec = new decisions.MergeDecision(simpleDecision);
        dec.action = "local";
        let value = decisions.buildDiffs(base, [dec], "merged");
        expect(value).toEqual([opPatch("source", dec.localDiff)]);
      });

      it("should build a simple merged diff for remote decision", () => {
        let dec = new decisions.MergeDecision(simpleDecision);
        dec.action = "remote";
        let value = decisions.buildDiffs(base, [dec], "merged");
        expect(value).toEqual([opPatch("source", dec.remoteDiff)]);
      });

      it("should build a simple merged diff for custom decision", () => {
        let dec = new decisions.MergeDecision(simpleDecision);
        dec.customDiff = dec.localDiff;
        dec.action = "custom";
        let value = decisions.buildDiffs(base, [dec], "merged");
        expect(value).toEqual([opPatch("source", dec.customDiff)]);
      });

      it("should build an empty merged diff for base decision", () => {
        let dec = new decisions.MergeDecision(simpleDecision);
        let value = decisions.buildDiffs(base, [dec], "merged");
        expect(isDiffEmpty(value)).toBe(true);
      });

      it("should build an interleaved merged diff for local_then_remote decision", () => {
        let dec = new decisions.MergeDecision(simpleDecision);
        dec.action = "local_then_remote";
        let value = decisions.buildDiffs(base, [dec], "merged");
        expect(value).toEqual([
          opPatch("source", dec.localDiff!.concat(dec.remoteDiff!)),
        ]);
      });

      it("should build an interleaved merged diff for remote_then_local decision", () => {
        let dec = new decisions.MergeDecision(simpleDecision);
        dec.action = "remote_then_local";
        let value = decisions.buildDiffs(base, [dec], "merged");
        expect(value).toEqual([
          opPatch("source", dec.remoteDiff!.concat(dec.localDiff!)),
        ]);
      });

      it("should build a diff for a clear_parent decision on a string", () => {
        let dec = new decisions.MergeDecision(simpleDecision);
        dec.action = "clear_parent";
        let value = decisions.buildDiffs(base, [dec], "merged");
        let expectedInner = opRemoveRange(0, 4);
        expectedInner.source = { decision: dec, action: "custom" };
        expect(value).toEqual([opPatch("source", [expectedInner])]);
      });
    });

    describe("filterDecisions", () => {
      let paths = [
        ["cells", 0, "outputs", 0],
        ["cells", 0, "outputs", 1],
        ["cells", 2, "outputs", 1],
        ["cells", 12, "outputs", 0, "data"],
      ];

      let decs: decisions.MergeDecision[] = [];
      for (let p of paths) {
        decs.push(new decisions.MergeDecision(p));
      }

      it("should pass all on shared prefix", () => {
        let value = decisions.filterDecisions(decs, ["cells"]);
        expect(value).toEqual(decs);
        for (let d of value) {
          expect(d.level).toBe(1);
        }
      });

      it("should return same instances", () => {
        let value = decisions.filterDecisions(decs, ["cells"]);
        expect(arraysEqual(value, decs)).toBe(true);
      });

      it("should filter on shared prefix", () => {
        let value = decisions.filterDecisions(decs, ["cells", 0]);
        expect(value).toEqual(decs.slice(0, 2));
        for (let d of value) {
          expect(d.level).toBe(2);
        }
      });

      it("should filter on common segment with skipLevels", () => {
        let value = decisions.filterDecisions(decs, ["outputs"], 2);
        expect(value).toEqual(decs);
        for (let d of value) {
          expect(d.level).toBe(3);
        }
      });

      it("should filter on shared prefix", () => {
        let value = decisions.filterDecisions(decs, ["outputs", 0], 2);
        expect(value).toEqual([decs[0], decs[3]]);
        for (let d of value) {
          expect(d.level).toBe(4);
        }
      });
    });

    describe("applyDecisions", () => {
      let baseObject = {
        source: "line 1\nline 2\nline 3 is longer\n",
        metadata: {
          secret: "foo!",
        },
      };

      let simpleObjectDecision: decisions.IMergeDecision = {
        local_diff: [opAddRange(3, ["line 4\n"])],
        remote_diff: [opAddRange(3, ["alternative line 4\n"])],
        common_path: ["source"],
      };

      it("should apply 'base' action on object", () => {
        let decs = [new decisions.MergeDecision(simpleObjectDecision)];
        let value = decisions.applyDecisions(baseObject, decs);
        expect(value).toEqual(baseObject);
      });

      it("should apply 'local' action on object", () => {
        let decs = [new decisions.MergeDecision(simpleObjectDecision)];
        decs[0].action = "local";
        let value = decisions.applyDecisions(baseObject, decs);
        expect(value.source).toEqual(baseObject.source + "line 4\n");
      });

      it("should apply 'remote' action on object", () => {
        let decs = [new decisions.MergeDecision(simpleObjectDecision)];
        decs[0].action = "remote";
        let value = decisions.applyDecisions(baseObject, decs);
        expect(value.source).toEqual(
          baseObject.source + "alternative line 4\n"
        );
      });

      it("should apply 'either' action on object", () => {
        let decs = [new decisions.MergeDecision(simpleObjectDecision)];
        decs[0].remoteDiff = decs[0].localDiff;
        decs[0].action = "either";
        let value = decisions.applyDecisions(baseObject, decs);
        expect(value.source).toEqual(baseObject.source + "line 4\n");
      });

      it("should handle multiple decisions with shared path", () => {
        let decs = [
          new decisions.MergeDecision({
            local_diff: [opAddRange(0, ["top "])],
            remote_diff: [opAddRange(0, ["not "])],
            common_path: ["metadata", "secret"],
          }),
          new decisions.MergeDecision({
            local_diff: [opAdd("foo", true)],
            remote_diff: [opAdd("foo", true)],
            common_path: ["metadata"],
          }),
          new decisions.MergeDecision({
            local_diff: [opRemoveRange(0, 1)],
            common_path: ["seq"],
          }),
          new decisions.MergeDecision({
            local_diff: [opRemoveRange(1, 1)],
            remote_diff: [opRemoveRange(1, 1)],
            common_path: ["seq"],
          }),
          new decisions.MergeDecision({
            local_diff: [opAdd("bar", 43)],
            remote_diff: [opAdd("bar", 12)],
            common_path: ["metadata"],
          }),
        ];
        decs[0].action = "local";
        decs[1].action = "either";
        decs[2].action = "local";
        decs[3].action = "either";
        decs[4].action = "local";
        let value = decisions.applyDecisions(
          { ...baseObject, seq: ["foo", "bar"] },
          decs
        );
        expect(value.metadata).toEqual({
          foo: true,
          bar: 43,
          secret: "top foo!",
        });
        expect(value.seq).toEqual([]);
      });
    });
  });
});
