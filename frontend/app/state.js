(function () {
  "use strict";
  const root = window.KGFoundation = window.KGFoundation || {};
  root.state = {
    workspace: null,
    loading: true,
    error: "",
    busy: false,
    creatingWorkspace: false,
    stage: "documents",
    g2: null,
    g2Loading: false,
    g2Busy: false,
    g2Error: "",
    g3: null,
    g3Loading: false,
    g3Busy: false,
    g3Error: "",
    g3Expanded: "",
    g3Ui: {},
  };
})();
