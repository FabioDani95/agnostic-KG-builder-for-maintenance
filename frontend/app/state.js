(function () {
  "use strict";
  const root = window.KGFoundation = window.KGFoundation || {};

  /**
   * One workspace state. Phases are named after the object the operator works
   * on (machine → documents → structure → graph); the internal development
   * checkpoints are not part of the product vocabulary.
   */
  root.state = {
    workspace: null,
    loading: true,
    error: "",
    busy: false,
    creatingWorkspace: false,
    phase: "machine",

    sources: [],

    structure: null,
    structureLoading: false,
    structureBusy: false,
    structureError: "",

    graph: null,
    graphLoading: false,
    graphBusy: false,
    graphError: "",

    /** Which source the three panes are currently describing. */
    activeSourceId: "",
    /** The single selection model shared by every surface. */
    selection: { kind: "", id: "" },
    /** Which representation of the active source fills the work pane. */
    view: "graph",
    /** Density and meaning filters; they apply to every view at once. */
    filters: {
      query: "",
      nodeType: "all",
      relationType: "all",
      onlyGaps: false,
      focus: false,
    },
    /** Inline rejection note, so a decision never goes through window.prompt. */
    rejectingSourceId: "",
    rejectionNote: "",
  };

  root.select = function select(kind, id) {
    root.state.selection = { kind: kind || "", id: id || "" };
  };

  root.clearSelection = function clearSelection() {
    root.state.selection = { kind: "", id: "" };
  };
})();
