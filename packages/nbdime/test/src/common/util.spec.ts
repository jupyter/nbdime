// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

import * as util from "../../../src/common/util";

describe("common", () => {
  describe("util", () => {
    describe("arraysEqual", () => {
      it("should return true for instance equality", () => {
        let a = [1, 2, 3];
        let value = util.arraysEqual(a, a);
        expect(value).toBe(true);
      });

      it("should return true for shallow equality", () => {
        let arrays = [
          [1, 2, 3],
          ["a", "b", "c"],
          [123, "text", true],
        ];
        for (let a of arrays) {
          let value = util.arraysEqual(a, a.slice());
          expect(value).toBe(true);
        }
      });

      it("should return true for both null", () => {
        let value = util.arraysEqual(null, null);
        expect(value).toBe(true);
      });

      it("should return false for one null input", () => {
        let a = [1, 2, 3];
        let value = util.arraysEqual(null, a);
        expect(value).toBe(false);

        value = util.arraysEqual(a, null);
        expect(value).toBe(false);
      });

      it("should return false for different length arrays", () => {
        let value = util.arraysEqual([1, 2, 3], [1, 2]);
        expect(value).toBe(false);

        value = util.arraysEqual([1, 2], [1, 2, 3]);
        expect(value).toBe(false);
      });

      it("should return false for deep comparison", () => {
        let value = util.arraysEqual([{ a: 1, b: 2 }], [{ a: 1, b: 2 }]);
        expect(value).toBe(false);
      });
    });

    describe("findSharedPrefix", () => {
      it("should return a copy on identical input", () => {
        let a = [1, 2, 3];
        let value = util.findSharedPrefix(a, a);
        expect(value).toEqual(a);
        expect(value).not.toBe(a); // Checking for instance equality
      });

      it("should return null for null inputs", () => {
        let value = util.findSharedPrefix(null, null);
        expect(value).toBe(null);

        value = util.findSharedPrefix(null, [1, 2]);
        expect(value).toBe(null);

        value = util.findSharedPrefix([1, 2], null);
        expect(value).toBe(null);
      });

      it("should return empty array for one or more empy inputs", () => {
        let value = util.findSharedPrefix([], []);
        expect(value).toEqual([]);

        value = util.findSharedPrefix([], [1, 2]);
        expect(value).toEqual([]);

        value = util.findSharedPrefix([1, 2], []);
        expect(value).toEqual([]);
      });

      it("should return empty array for disjoint inputs", () => {
        let value = util.findSharedPrefix([1, 2, 3], ["a", "b", "c"]);
        expect(value).toEqual([]);
      });

      it("should return empty array for inputs that overlap after start", () => {
        let value = util.findSharedPrefix([1, 2, 3, 4], [5, 2, 3, 4]);
        expect(value).toEqual([]);
      });

      it("should find prefix of single element arrays", () => {
        let value = util.findSharedPrefix([1], [1]);
        expect(value).toEqual([1]);

        value = util.findSharedPrefix(["text"], ["text"]);
        expect(value).toEqual(["text"]);
      });

      it("should find prefix of muliple element arrays that are equal", () => {
        let value = util.findSharedPrefix([1, 2, 3], [1, 2, 3]);
        expect(value).toEqual([1, 2, 3]);

        value = util.findSharedPrefix(["text", "abc"], ["text", "abc"]);
        expect(value).toEqual(["text", "abc"]);
      });

      it("should find prefix of muliple element arrays that are not equal", () => {
        let value = util.findSharedPrefix([1, 2, 3, 4, 5], [1, 2, 3, 6, 7]);
        expect(value).toEqual([1, 2, 3]);

        value = util.findSharedPrefix(
          ["text", "abc", "foo"],
          ["text", "abc", "bar"]
        );
        expect(value).toEqual(["text", "abc"]);
      });
    });

    describe("isPrefixArray", () => {
      it("should return true for object equality", () => {
        let a = [1, 2, 3];
        let value = util.isPrefixArray(a, a);
        expect(value).toBe(true);
      });

      it("should return true for null parent", () => {
        let a = [1, 2, 3];
        let value = util.isPrefixArray(a, a);
        expect(value).toBe(true);
      });

      it("should return true for null parent", () => {
        let value = util.isPrefixArray(null, null);
        expect(value).toBe(true);

        value = util.isPrefixArray(null, [1, 2, 3]);
        expect(value).toBe(true);
      });

      it("should return true for empty parent", () => {
        let value = util.isPrefixArray([], null);
        expect(value).toBe(true);

        value = util.isPrefixArray([], []);
        expect(value).toBe(true);

        value = util.isPrefixArray([], [1, 2, 3]);
        expect(value).toBe(true);
      });

      it("should return false for null child, with non null/empty parent", () => {
        let value = util.isPrefixArray([1], null);
        expect(value).toBe(false);
      });

      it("should return false if child is shorter than parent", () => {
        let value = util.isPrefixArray([1], []);
        expect(value).toBe(false);

        value = util.isPrefixArray([1, 2, 3, 4], [1, 2, 3]);
        expect(value).toBe(false);
      });

      it("should return true if child is equal to parent", () => {
        let value = util.isPrefixArray([1], [1]);
        expect(value).toBe(true);

        value = util.isPrefixArray([1, 2, 3, 4], [1, 2, 3, 4]);
        expect(value).toBe(true);

        value = util.isPrefixArray(["abc", "def", 0], ["abc", "def", 0]);
        expect(value).toBe(true);
      });

      it("should return true if entire parent matches start of child", () => {
        let value = util.isPrefixArray([1], [1, 2]);
        expect(value).toBe(true);

        value = util.isPrefixArray([1, 2, 3], [1, 2, 3, 4]);
        expect(value).toBe(true);

        value = util.isPrefixArray(["abc", "def"], ["abc", "def", 0]);
        expect(value).toBe(true);
      });

      it("should return false if entire parent matches non-start of child", () => {
        let value = util.isPrefixArray([2], [1, 2]);
        expect(value).toBe(false);

        value = util.isPrefixArray([2, 3, 4], [1, 2, 3, 4]);
        expect(value).toBe(false);

        value = util.isPrefixArray(["def"], ["abc", "def", 0]);
        expect(value).toBe(false);
      });
    });

    describe("accumulateLengths", () => {
      it("should handle an empty array", () => {
        let value = util.accumulateLengths([]);
        expect(value).toEqual([]);
      });

      it("should handle an single item array", () => {
        let value = util.accumulateLengths(["abc"]);
        expect(value).toEqual([3]);
      });

      it("should handle multiple strings", () => {
        let value = util.accumulateLengths(["abc", "foo", "0xdead"]);
        expect(value).toEqual([3, 6, 12]);
      });

      it("should handle multiple strings with newlines at end", () => {
        let value = util.accumulateLengths(["abc\n", "foo\n", "0xdead\n"]);
        expect(value).toEqual([4, 8, 15]);
      });

      it("should handle multiple strings with newlines randomly placed", () => {
        let value = util.accumulateLengths(["\nabc", "foo\n", "0xde\nad"]);
        expect(value).toEqual([4, 8, 15]);
      });
    });

    describe("hasEntries", () => {
      it("should return false for null", () => {
        let value = util.hasEntries(null);
        expect(value).toBe(false);
      });

      it("should return false for empty array", () => {
        let value = util.hasEntries([]);
        expect(value).toBe(false);
      });

      it("should return true for array with falsy entry", () => {
        let value = util.hasEntries([0]);
        expect(value).toBe(true);
      });

      it("should return true for array with truthy entry", () => {
        let value = util.hasEntries([4]);
        expect(value).toBe(true);
      });
    });

    describe("buildSelect", () => {
      it("should create an empty select", () => {
        let value = util.buildSelect([]);
        expect(value.outerHTML).toEqual("<select></select>");
      });

      it("should reuse a given select", () => {
        const select = document.createElement("select");
        let value = util.buildSelect([], select);
        expect(value).toBe(select);
      });

      it("should create a select with options", () => {
        let value = util.buildSelect(["foo", "bar", "<div>boo</div>"]);
        expect(value.outerHTML).toEqual(
          "<select>" +
            "<option>foo</option>" +
            "<option>bar</option>" +
            "<option>&lt;div&gt;boo&lt;/div&gt;</option>" +
            "</select>"
        );
      });
    });
  });
});
