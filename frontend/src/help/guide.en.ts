// The guide in English: the same chapters, sections and addresses as guide.ts.
import type { GuideChapter } from "./guide";

export const GUIDE_EN: GuideChapter[] = [
  {
    slug: "panoramica",
    title: "Overview",
    icon: "graph",
    lead:
      "The application reads the manual of a machine and turns it into a maintenance graph: a map that links symptoms and error codes to their causes, and causes to the actions that fix them. Every link carries the page and the words of the manual it comes from.",
    sections: [
      {
        id: "a-cosa-serve",
        heading: "What it is for",
        body: [
          "Facing a fault, a maintenance technician starts from what they see: a symptom, or a code on the display. The graph lets them start there and reach the possible causes and the fixes, without leafing through the manual.",
          "The graph is made to be checked: every link says whether it was verified, by whom, and shows the text of the manual that supports it.",
        ],
      },
      {
        id: "cosa-contiene",
        heading: "What a graph holds",
        body: [
          "Six kinds of elements, always the same for every manual:",
          [
            "Machine: the machine the manual is about, one per graph.",
            "Symptom: what can be observed (for example “the pump does not start”).",
            "Error code: an alarm or a code shown by the machine.",
            "Cause: the technical reason that can explain a symptom or a code.",
            "Action: the fix for the cause, or a check to make, or a call for service when the manual gives nothing else.",
            "Component: the part of the machine involved.",
          ],
          "The full schema, with every link allowed, is in the Ontology section.",
        ],
      },
      {
        id: "percorso",
        heading: "The path in short",
        body: [
          [
            "You upload the PDF manual and check the machine data.",
            "The extraction reads the manual and builds the graph; you can follow it live.",
            "If doubts remain, some reach you as simple questions.",
            "You check the graph and approve it.",
            "From then on the graph is ready to be consulted.",
          ],
        ],
      },
      {
        id: "dove-trovare",
        heading: "Where to find things",
        body: [
          "The dark bar on the left leads to the places of the application; the bar at the top says where you are and holds the actions of the page.",
          [
            "The logo takes you back to the list of all graphs.",
            "Your turn gathers what waits for your answer or approval; the orange number says how many graphs are on hold for you.",
            "Runs lists every extraction made, with times and costs.",
            "Ontology shows the schema every graph follows.",
            "While an extraction is running a blue light appears: it takes you straight to the growing graph.",
            "At the bottom: the language (IT or EN, it switches the whole interface), this guide and the settings.",
          ],
          "Pointing at an icon shows its name.",
        ],
      },
    ],
  },
  {
    slug: "nuovo-grafo",
    title: "Making a graph",
    icon: "plus",
    lead:
      "A graph is born in three steps: choose the manual, check the machine data, decide who answers the doubts. The summary on the right shows the expected time and cost before you start.",
    sections: [
      {
        id: "manuale",
        heading: "1. The manual",
        body: [
          "You can drop a PDF on the area or choose it from the computer. If that PDF is already in the library the application recognises it: the new extraction becomes a new version of the graph that already exists.",
          "Otherwise choose “From the library” to run the extraction again on a manual already uploaded. From the page of a manual, “New version” does the same.",
        ],
      },
      {
        id: "macchina",
        heading: "2. The machine",
        body: [
          "As soon as the PDF is uploaded, a light model reads the first pages and fills in machine, brand, model and type by itself. While it reads you only see a turning mark; then the fields fill in and stay editable.",
          "It reads one page at a time until it has enough text, five pages at most; if the PDF is a scan without text it looks at the image of the cover. It only writes what it finds: if a value is not there, the field stays empty.",
          "Always check the fields before starting. Only the name of the machine is required.",
        ],
      },
      {
        id: "dubbi",
        heading: "3. Who answers the doubts",
        body: [
          "During the extraction some links remain uncertain. You can decide who checks them:",
          [
            "Agent only: a model answers every doubt. Only the final approval is left to you.",
            "Agent, then me: the agent answers the doubts it can settle; those it is not sure about come to you.",
            "Only me: the doubts come to you.",
          ],
          "In any case a person gets a limited number of questions, usually 10 (it can be changed in the settings). The most important come first; the others stay in the graph as “unverified”.",
        ],
      },
      {
        id: "stima",
        heading: "Estimated time and cost",
        body: [
          "The estimate comes from the two past extractions whose number of pages is closest to your manual: that is why it is a range, for example “2–3 min”. When the two values are the same you see one value, for example “~5 min”.",
          "It is a guide, not a promise: a manual with many diagnostic tables takes more work than one with few.",
        ],
      },
      {
        id: "avvio",
        heading: "Starting",
        body: [
          "“Start extraction” becomes active when there is a manual and the name of the machine. If it cannot start, the reason is written under the button. Only one extraction can run at a time.",
          "Every extraction has a spending ceiling: if the estimate does not fit, the start is refused with a message.",
        ],
      },
    ],
  },
  {
    slug: "estrazione",
    title: "How the extraction works",
    icon: "activity",
    lead:
      "The extraction goes through six stations, always in the same order. On the run screen you see them on the left, each with a light: grey waiting, blue running, green done.",
    sections: [
      {
        id: "leggi",
        heading: "Read",
        body: [
          "The PDF is split into small pieces: blocks of text and rows of tables, each with its exact place on the page. Pages without text go through character recognition. No model works here.",
          "From now on every piece of information in the graph can point to the exact line of the manual it comes from.",
        ],
      },
      {
        id: "mappa",
        heading: "Map",
        body: [
          "A model looks at every page and labels it: diagnostic, procedure, parts, other. Only the pages useful for diagnosis are read in depth, plus those right next to them so nothing is lost; when in doubt a page is included.",
          "The pages to read are grouped into reading units, trying not to split the tables. An agent confirms the map before going on.",
        ],
      },
      {
        id: "estrai",
        heading: "Extract",
        body: [
          "Each unit is read by a model that finds symptoms, codes, causes, actions and components and links them, saying where it read them. Each unit is read twice, independently: together the two reads miss less, and when they agree they give confidence.",
          "A wrong detail does not throw anything away: it is noted and the work goes on. If a row of a diagnostic table is used by neither read, it is read again on purpose.",
        ],
      },
      {
        id: "controlla",
        heading: "Check",
        body: [
          "Every link looks for independent “witnesses”:",
          [
            "page structure: the two elements are written in the same row or the same block;",
            "agreement of the two reads: both found it;",
            "verifier: if the other two are missing, a model reads only the quoted text again and says whether it really expresses that link.",
          ],
          "With two witnesses the link is verified (green). With only one, or with witnesses that disagree, it is in doubt (yellow) and becomes a question. With no witness it is discarded: it stays out of the graph, but listed in the report.",
        ],
      },
      {
        id: "unisci",
        heading: "Merge",
        body: [
          "The same symptom or the same cause can appear in several places of the manual with slightly different words. Here they become one element. Uncertain likenesses are judged by a model; elements with different codes or numbers are never merged. The other names stay recorded.",
          "This is also when the links between the machine and its components and codes are added: they do not come from the text, the system adds them.",
        ],
      },
      {
        id: "chiedi",
        heading: "Ask",
        body: [
          "Links in doubt that come from the same place of the manual become a single question. The agent answers first, if chosen; what is left comes to you, up to the set limit.",
          "At the end of the run a box says how it went and what the next step is.",
        ],
      },
      {
        id: "fermare",
        heading: "Stopping a run",
        body: [
          "“Stop” interrupts the extraction in progress. The work done so far stays saved.",
          "You can also leave the screen: the extraction goes on, and the blue light in the bar on the left takes you back to it.",
        ],
      },
    ],
  },
  {
    slug: "domande",
    title: "Questions and approval",
    icon: "question",
    lead:
      "Questions settle the doubts the system cannot settle by itself. They are few and clear: they show the text of the manual and what the system proposes, and you answer without looking elsewhere.",
    sections: [
      {
        id: "tocca-a-te",
        heading: "Your turn",
        body: [
          "The Your turn section gathers three groups:",
          [
            "Waiting for you: graphs on hold until you answer or approve. Each one shows its next step, for example “Answer the 10 questions”.",
            "Running: the extraction that is working.",
            "Doubts in approved graphs: questions left unanswered in graphs already approved. They block nothing.",
          ],
        ],
      },
      {
        id: "rispondere",
        heading: "How to answer",
        body: [
          "Every question shows the lines of the manual involved, with their page, and one or more statements of the system. “Open page” shows the original page.",
          [
            "“Yes, it is right” confirms everything.",
            "“Only in part” lets you choose which statements to keep.",
            "“No” discards the proposal.",
            "For some questions you can write the text yourself, for example when a page cannot be read.",
          ],
          "“Details” shows the proposal in its technical form, if you want to check it to the end.",
        ],
      },
      {
        id: "applicare",
        heading: "Applying the answers",
        body: [
          "When you have answered every question, “Apply the answers” restarts the run from where it stopped: your answers go into the graph without redoing the extraction.",
          "A confirmation or a rejection of yours counts more than the automatic checks.",
        ],
      },
      {
        id: "approvare",
        heading: "Approving the graph",
        body: [
          "The last step is the approval: you check the graph and choose “Approve” or “Reject”. In the application the approval is always a person's.",
          "The graphs of the evaluation campaign were approved automatically and say so with “Approved by the system”. If you answer a question of one of these graphs, the first answer makes a copy of it where you go on working: the original does not change.",
        ],
      },
      {
        id: "passi",
        heading: "Where a graph stands",
        body: [
          "On the page of a manual the current version shows three steps: extraction, questions, approval. A green light with a tick is a step done, orange a step waiting for you, red a step that failed.",
          "Under the steps there is always one main button: the next step to take.",
        ],
      },
    ],
  },
  {
    slug: "grafo",
    title: "Reading the graph",
    icon: "search",
    lead:
      "The graph fills the middle of the screen. On the left there are filters, legend and version data; on the right, when you choose something, the evidence behind it.",
    sections: [
      {
        id: "muoversi",
        heading: "Moving in the graph",
        body: [
          [
            "Drag to turn it, use the wheel to come closer or move away.",
            "At the first touch the graph stops where it is, so you can explore it calmly. “Re-arrange” makes it move again; “Fit” brings it all back on screen.",
            "Pointing at a node shows its name; in the settings you can keep the names always visible.",
          ],
        ],
      },
      {
        id: "colori",
        heading: "Colours and lines",
        body: [
          "Each kind of element has its colour, shown in the legend with the number of elements. Links show their state with their colour:",
          [
            "green: verified;",
            "dashed yellow: in doubt;",
            "grey: proposed, not checked yet;",
            "faint grey: added by the system to link the machine to its components and codes.",
          ],
          "Discarded links do not appear. With the filter at the top left you see all links, only the verified ones or only those in doubt.",
        ],
      },
      {
        id: "cercare",
        heading: "Searching a symptom or a code",
        body: [
          "Type in the search field at the top (the “/” key takes the cursor there) and choose a result. The graph highlights the diagnostic path: from the symptom or code to the causes, from the causes to the actions and components. The rest fades. “Show the whole graph” goes back to the full view.",
        ],
      },
      {
        id: "prove",
        heading: "The evidence",
        body: [
          "Choosing a node or a link opens the evidence on the right: the lines of the manual with their page, the state, the witnesses that support it and, if someone decided, who. “Open page” shows the original page with the quoted text highlighted, when its position is known.",
          "The panel closes with the cross or with the Esc key.",
        ],
      },
      {
        id: "dal-vivo",
        heading: "The growing graph",
        body: [
          "During an extraction the graph builds up before your eyes: new nodes appear as they are found and links change colour when they are checked. At the bottom you see the counters and the last relation found.",
          "Past extractions can be replayed with “Replay the run”, at 1×, 4× or 16× speed, with pause. Replaying costs nothing: it calls no model.",
        ],
      },
    ],
  },
  {
    slug: "esecuzioni",
    title: "Runs, times and costs",
    icon: "activity",
    lead: "Each extraction is a run, and each run produces a version of the graph. The time and cost of each are always in sight.",
    sections: [
      {
        id: "versioni",
        heading: "Versions",
        body: [
          "A manual can have several versions of its graph: repeated extractions, made with different settings, or copies born from the answers to the questions. The page of the manual lists them all; the most recent is the current version.",
          "With the version menu, on the graph screen, you move from one version to another.",
        ],
      },
      {
        id: "registro",
        heading: "The Runs page",
        body: [
          "It lists every run of every manual, newest first, with outcome, duration and cost. You can see only those started from the interface or only those of the evaluation campaign, and sort by column. A row leads to the right step: the graph, the questions or the run in progress.",
        ],
      },
      {
        id: "costi",
        heading: "How the cost is made",
        body: [
          "The cost is that of the models used: the map, the two reads of each unit, the verifier, the agent on the doubts. Every call is recorded with its cost, and every extraction has a ceiling it cannot go past.",
          "Reading the machine data after the upload costs a fraction of a cent. Replaying a run costs nothing, and usually neither does applying the answers: the work already done is not repeated.",
        ],
      },
    ],
  },
  {
    slug: "ontologia",
    title: "The ontology",
    icon: "schema",
    lead:
      "The ontology is the fixed schema every graph follows: which kinds of elements exist and which links are allowed between them. It is the same for every manual, so graphs can be compared and used the same way.",
    sections: [
      {
        id: "schema",
        heading: "The schema",
        body: [
          "The Ontology page draws the schema with the same colours as the graph, so it doubles as a legend. The main path runs from left to right: symptom or code, then cause, then action and component.",
        ],
      },
      {
        id: "chi-crea",
        heading: "Who makes the links",
        body: [
          "The solid line marks links extracted by the model, each with its evidence in the manual. The dashed line marks those added by the system: they link the machine to its components and its codes.",
          "Under the schema you find the description of each kind and of each link, as written in the schema.",
        ],
      },
    ],
  },
  {
    slug: "impostazioni",
    title: "Settings",
    icon: "settings",
    lead:
      "The gear at the bottom left opens the settings. They apply to the new extractions started from here; an extraction already started, even when it resumes after your answers, keeps those it started with.",
    sections: [
      {
        id: "chiave",
        heading: "OpenAI key",
        body: [
          "Usually the key already set up on the computer is used. If you write another one, it will be used for the new extractions and for reading the machine data. The key stays on this computer and is never shown: you only see its last four characters. “Use .env” goes back to the usual one.",
        ],
      },
      {
        id: "estrazione",
        heading: "Extraction",
        body: [
          [
            "Reasoning: how much the model thinks before answering. More reasoning can find subtler links, but takes more time and costs more.",
            "Reads per unit: how many times each part of the manual is read. Two is the advised value, because the agreement of two reads acts as a witness. One costs less but checks less; three is more careful.",
          ],
        ],
      },
      {
        id: "agente",
        heading: "Agent",
        body: ["The model and the reasoning of the agent that answers the doubts in your place, according to the choice made in “Who answers the doubts”."],
      },
      {
        id: "domande",
        heading: "Questions",
        body: [
          "The most questions a person gets in one extraction. The most important come first; beyond the limit the doubts stay in the graph as unverified.",
        ],
      },
      {
        id: "grafo",
        heading: "Graph",
        body: [
          [
            "Relations added by the code: shows or hides the links between the machine and its components and codes.",
            "Names always shown on the nodes: writes the name next to every node instead of showing it only on pointing.",
          ],
          "These two choices apply at once, in every graph.",
        ],
      },
    ],
  },
];
