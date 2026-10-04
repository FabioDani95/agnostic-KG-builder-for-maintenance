// The guide in English: the same chapters, sections and addresses as guide.ts.
import type { GuideChapter } from "./guide";

export const GUIDE_EN: GuideChapter[] = [
  {
    slug: "panoramica",
    title: "Overview",
    icon: "graph",
    lead:
      "The application reads a machine's manual and turns it into a maintenance graph: a map linking symptoms and error codes to possible causes, checks and interventions. Extracted links retain the pages and words of the manual they are based on, so you can understand the path and check its evidence.",
    sections: [
      {
        id: "a-cosa-serve",
        heading: "What it is for",
        body: [
          "Facing a fault, a maintenance technician starts from what they see: a symptom, or a code on the display. The graph lets them start there and reach the possible causes and the fixes, without leafing through the manual.",
          "The graph is made to be checked: for each extracted relation you can see its verification status, the evidence in the manual and any decision by an agent or a person. A relation is a link between two elements; the elements are also called nodes.",
          "For example, if a manual links “the pump does not start” to “no power supply” and prescribes “check the power supply”, the graph can represent that path with three nodes. If the manual lists several causes, you will see several branches: you need to assess which one matches the situation you observe.",
          "Start your consultation with the right machine and manual version. The graph organises what was extracted: a symptom missing from the results does not prove that the fault is impossible or that the manual does not discuss it. Opening the cited pages also helps you read the context and conditions of an intervention.",
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
          "Symptoms and causes play different roles: “the pump does not start” describes what you observe; “no power supply” offers an explanation. Likewise, “check the cable” is a check, whereas “replace the cable” is an intervention: an action appearing in a path does not always mean that a solution has already been found.",
          "Some manuals prescribe a check or remedy without naming the cause. In those cases the system may assign a name to represent the branch; the node panel indicates “Cause not written in the manual”. Read the evidence to distinguish what the source states from the wording used to organise it.",
          "A node can have several names and appear on several pages. A relation can have several occurrences, meaning passages in the manual where it is described: each retains its own evidence and conditions.",
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
          "If you are learning, you can start with a graph already in the library: open it, search for a symptom, choose a relation and compare it with the original page. Replaying a run then lets you observe the stages of construction without starting another extraction.",
          "Keep two checks separate: approval concerns the version as a whole, whereas green or yellow concerns an individual relation. An approved graph can retain doubts; you can identify and filter them even after approval.",
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
          "In the library you can search by name, brand, model or kind of machine and choose “All”, “To review” or “Approved”. “To review” also includes graphs that still have open questions. Opening a manual's row shows its PDF, current version and version history; the action icon on the row takes you directly to the graph or run.",
          "You can read the Guide in order using the previous and next chapter links. The index on the left changes chapter; “On this page”, when visible, takes you to individual sections. You can return to an application screen from the sidebar at any time.",
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
          "Choose the document for the model and revision you want to consult, with readable diagnostic sections. A PDF with selectable text makes reading easier; a scan also depends on image quality and the availability of character recognition. Successful upload does not guarantee that every page is readable.",
          "After uploading, check the file name and page count. “Change” lets you choose another PDF before starting. If the file is damaged or is not a PDF, the application shows the problem and lets you choose another one.",
          "Recognition of an existing manual is based on the file's contents, not its name. A new extraction of the same PDF retains the previous versions; a different PDF, even for the same machine, is treated as another manual.",
        ],
      },
      {
        id: "macchina",
        heading: "2. The machine",
        body: [
          "As soon as the PDF is uploaded, a light model reads the first pages and fills in brand, model and kind of machine by itself (for example “dust collector”). While it reads you only see a turning mark; then the fields fill in and stay editable. The name of the manual in the library is made of these three.",
          "It reads one page at a time until it has enough text, five pages at most; if the PDF is a scan without text it looks at the image of the cover. It only writes what it finds: if a value is not there, the field stays empty.",
          "Always check the fields before starting. At least the brand or the model is needed.",
          "For a new manual you can correct the data after the automatic reading: use the brand and model designation as printed in the document and a short kind of machine, such as “compressor”. These fields help you recognise the manual in the library; reading the first pages identifies it, while extraction of diagnostic information happens after you start.",
          "If automatic identification fails, you can fill in the fields yourself. If you choose a manual from the library or upload a PDF recognised as a duplicate, the recorded data is reused and the fields are locked.",
        ],
      },
      {
        id: "dubbi",
        heading: "3. Who answers the doubts",
        body: [
          "During the extraction some links remain uncertain. You can decide who checks them:",
          [
            "Agent only: a model reviews the doubts without normally passing them to you; those it cannot settle may stay open. Final approval remains yours.",
            "Agent, then me: the agent answers the doubts it can settle; those it is not sure about come to you.",
            "Only me: the doubts come to you.",
          ],
          "In any case a person gets a limited number of questions, usually 10 (it can be changed in the settings). The most important come first; the others stay in the graph as “unverified”.",
          "“Agent, then me” is the interface's initial choice. “Only me” lets you review extraction doubts directly; “Agent only” assigns that review to the model. This choice concerns doubts: the page map is still submitted to the agent, and approval of a new graph started here requires a person.",
          "One question can group several statements from the same passage, so the question limit does not equal the number of relations reviewed. Reducing the limit reduces the work asked of you, but may leave more relations in doubt.",
        ],
      },
      {
        id: "stima",
        heading: "Estimated time and cost",
        body: [
          "The estimate uses reference campaign runs for the two manuals whose page counts are closest to yours. It shows the range between their times and costs, for example “2–3 min”. If only one reference is available, or the values match, you see a single approximate value, for example “~5 min”.",
          "It is a guide, not a promise: a manual with many diagnostic tables takes more work than one with few.",
          "The summary shows costs in USD. The estimate is not recalculated in detail for your chosen model, reasoning or number of reads: changing the settings can make actual time and cost differ from the references. During the run you can follow the updated values.",
          "If no suitable reference runs are available, a dash appears and starting is blocked because the system cannot estimate the cost. Uploading the same file again does not add the missing references.",
        ],
      },
      {
        id: "avvio",
        heading: "Starting",
        body: [
          "“Start extraction” becomes active when a manual has been chosen, at least the brand or model is present, and no operation or run prevents it from starting. The summary shows the reason for any block near the button. Only one extraction can run at a time.",
          "Before pressing the button, check the manual, machine data, who will answer the doubts and the extraction settings. Starting creates a new version and opens the screen where you can follow its construction.",
          "The system compares the highest estimated cost with the spending still available, including the allowance for activities started from the interface. If it does not fit within the limits, starting is refused with a message; those limits cannot be changed in the Settings window.",
          "If a run is already in progress, “Follow it” takes you to its screen. Wait for it to finish before starting another. An error message while starting does not mean that the graph was completed: check the manual's page to see whether a version was created.",
        ],
      },
    ],
  },
  {
    slug: "estrazione",
    title: "How the extraction works",
    icon: "activity",
    lead:
      "Construction follows six main stations: Read, Map, Extract, Check, Merge and Ask. Some corrections require further checks. On the run screen you see the stations on the left: grey means waiting, blue running and green done. A green station means the stage has finished, not that every relation is verified.",
    sections: [
      {
        id: "leggi",
        heading: "Read",
        body: [
          "The PDF is split into small pieces: blocks of text and rows of tables, each linked to its page and, when available, the text's position. If a page has little text or corrupted text, the system attempts character recognition when available and within the configured limits. No language model is used at this stage.",
          "Each piece receives a reference that later stages can cite. This makes it possible to return to the source without asking the model to copy the passage from memory.",
          "In tables the system tries to keep the problem, cause and remedy together, with the column headings. A blurred scan or a complex table may still lose text or structure: if a passage seems incomplete, compare it with the original page.",
        ],
      },
      {
        id: "mappa",
        heading: "Map",
        body: [
          "Two independent readings classify the pages as diagnostic, procedure, parts or other, using an outline of their contents. A page labelled diagnostic by at least one reading is included. Some continuations are also added: for example a procedure next to a diagnostic page, or a page between two diagnostic pages.",
          "The pages to read are grouped into reading units, trying not to split the tables. An agent confirms the map before going on.",
          "A reading unit is a portion of the manual given to the model with useful context. It does not necessarily correspond to an entire page: a short document with many tables may require several units.",
          "The map focuses the work on diagnosis instead of turning every page into a node. Selection does not guarantee that every useful piece of information has been found; pages without readable text are identified separately.",
        ],
      },
      {
        id: "estrai",
        heading: "Extract",
        body: [
          "The model reads each unit and proposes symptoms, codes, causes, actions and components, with their links and text references. By default each unit is read twice, independently; in Settings you can choose between one and three reads. The proposals are collected together and their agreement can contribute to verification.",
          "The system checks that citations exist and that links follow the ontology. Proposals with errors are reported; valid ones can continue. Some unused diagnostic rows receive an additional reading attempt, within the procedure's limits.",
          "The graph you see growing at this stage still contains proposals. A newly appearing node or a grey line is not yet a confirmed result: it needs to pass the subsequent checks.",
          "When the manual distinguishes conditions, prerequisites, warnings or test results, the system tries to retain them with the link. They are part of the branch's meaning and need to be considered when choosing an intervention.",
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
            "verifier: when structure and agreement are insufficient, a model rereads the passage with its citations and available context and assesses whether it actually supports the link.",
          ],
          "With two witnesses the link is verified (green). With only one, or with witnesses that disagree, it is in doubt (yellow) and becomes a question. With no witness it is discarded: it stays out of the graph, but listed in the report.",
          "“Verified” describes the documentary support found for that relation. It is not a confidence percentage or confirmation that the cause explains the fault in the machine in front of you. Agreement between two reads is a useful check, but even agreeing reads can be wrong.",
          "The evidence panel shows which witnesses contributed. A subsequent review decision can confirm or reject the relation; reading the decision and cited passage is therefore more informative than the colour alone.",
        ],
      },
      {
        id: "unisci",
        heading: "Merge",
        body: [
          "The same symptom or the same cause can appear in several places of the manual with slightly different words. Here they become one element. Uncertain likenesses are judged by a model; elements with different codes or numbers are never merged. The other names stay recorded.",
          "This is also when the links between the machine and its components and codes are added: they do not come from the text, the system adds them.",
          "Merging two names avoids duplicates while retaining alternative names and citations. It does not mean combining every possible cause or confusing distinct components: similar wording alone is insufficient to decide they are the same thing.",
          "If the same link appears in several passages, it can become a single line in the graph with several occurrences. The evidence and conditions of each remain separate in the panel. The line can be green because one occurrence is verified while another passage remains in doubt: check the occurrence relevant to your case.",
        ],
      },
      {
        id: "chiedi",
        heading: "Ask",
        body: [
          "Links in doubt that come from the same place of the manual become a single question. The agent answers first, if chosen; what is left comes to you, up to the set limit.",
          "At the end of the run a box says how it went and what the next step is.",
          "Doubts can concern what a row says, whether two similar names refer to the same thing or an unreadable page. Grouping them by passage lets you compare several statements with the same source without answering one question for every line in the graph.",
          "An answer may require separating elements or checking part of the result again. This is why you may see a further check after merging or new questions after applying the first answers. Relations that remain unresolved retain their doubtful status.",
        ],
      },
      {
        id: "fermare",
        heading: "Stopping a run",
        body: [
          "“Stop” interrupts the extraction in progress. The work done so far stays saved.",
          "You can also leave the screen: the extraction goes on, and the blue light in the bar on the left takes you back to it.",
          "Use “Stop” when you want to interrupt the work itself; changing page does not interrupt it. Time and cost already incurred are not cancelled. Data saved before interruption is not equivalent to a completed and approved version.",
          "If the run fails or is interrupted, the library and run log let you see where it stopped. “New version” starts a new extraction of the manual; “Resume” in a replay only resumes playback of the events.",
        ],
      },
    ],
  },
  {
    slug: "domande",
    title: "Questions and approval",
    icon: "question",
    lead:
      "Questions help settle extraction doubts. They present the available text and what the system proposes; when the passage is insufficient, you can open the original page. Answers update individual decisions, while final approval concerns the entire version of the graph.",
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
          "Open a row to go to the indicated step. The orange number in the sidebar counts manuals whose current version is waiting for a person: it is not the total number of questions or doubtful relations.",
          "This page summarises current versions. To review an earlier version, open the manual and choose its entry in the history. If you answer doubts in a campaign version, the application takes you to the copy created for your answers.",
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
          "Read “In the manual” first, then each statement under “The system proposes”. Ask whether that passage actually links the indicated problem, cause and action, including the conditions. A technically plausible intervention should not be confirmed if the text shown does not support it.",
          "For example, if a question contains three statements and the source supports only the first and third, choose “Only in part”, select 1 and 3, then press “Keep the chosen statements”. The others are rejected. At least one selection is required; if none is supported, use “No”.",
          "Questions about names use “Yes, the same” or “No, different”: assess whether the names actually refer to the same element. For an unreadable page you can choose to skip it or submit a transcription. The transcription is kept in the report for a subsequent extraction; it does not automatically generate new nodes in the current version.",
          "Questions appear one at a time and each submitted answer is saved. You can leave the screen and return to complete the remaining questions; selections or text you have not submitted are not a recorded answer.",
        ],
      },
      {
        id: "applicare",
        heading: "Applying the answers",
        body: [
          "Once you have answered every question presented, “Apply the answers” resumes the run using the saved work and updates the graph with your decisions. Completed parts are reused; checks needed after the changes may require additional work. Wait for the outcome before assessing the updated graph.",
          "A confirmation or a rejection of yours counts more than the automatic checks.",
          "Submitting an answer and applying it are separate steps: approval stays blocked while answers remain unapplied. After application, you can return to the graph, open the affected relations and check the recorded decision in the evidence.",
          "The page also indicates how many doubts remain beyond the question limit: those relations may be present, but remain outside the verified part. Resuming requires that no other run is active and that room remains within the spending limits; if blocked, the reason is shown.",
        ],
      },
      {
        id: "approvare",
        heading: "Approving the graph",
        body: [
          "The final step is approval. On the graph you will find “Approve” once every question presented has been answered and the answers have been applied; the questions screen also lets you choose “Reject”. To record the decision, the run resumes briefly using its saved state. A person decides for graphs started from the interface.",
          "The graphs of the evaluation campaign were approved automatically and say so with “Approved by the system”. If you answer a question of one of these graphs, the first answer makes a copy of it where you go on working: the original does not change.",
          "Before approving, check that you are on the right version, search for some symptoms or codes from the manual and compare the paths with the cited pages. Also assess doubtful relations and action contexts: a version can be approved while retaining unverified relations.",
          "Approval records your decision on the overall result; it does not turn every yellow line green. “Reject” records that the version is not approved, without deleting the manual or its history. “Approved by the system” indicates an automatic workflow decision, not a human review of the information.",
        ],
      },
      {
        id: "passi",
        heading: "Where a graph stands",
        body: [
          "On the page of a manual the current version shows three steps: extraction, questions, approval. A green light with a tick is a step done, orange a step waiting for you, red a step that failed.",
          "Under the steps there is always one main button: the next step to take.",
          "“Running” invites you to follow construction; open questions need answers and then application; “Check and approve” takes you to final review. If the version failed, you can inspect the interruption point. These indicators describe the workflow, whereas “Verified”, “In doubt” and “Excluded” counts describe relations.",
          "Do not infer completion from the node count or the end of extraction alone. Check the version's outcome and next step: construction can be finished while still awaiting your approval.",
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
          "Choose a node to read its name, citations and relations; choose a line to understand the link between its ends. From the panel you can move from a node to a relation and from the relation to its nodes, continuing to explore the path.",
          "The positions in space make the graph easier to explore. Two nearby nodes do not necessarily have a relation: the meaning comes from the lines and their descriptions. “Re-arrange” and “Fit” change the view without changing the saved information.",
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
          "A node's colour indicates its type, while a line's colour indicates the relation's status. A coloured node is not, by itself, a verified element: open the link you are interested in to read its evidence.",
          "Filters change the view without deleting data. Nodes that do not participate in the displayed relations may disappear from view; the legend and bottom bar counts summarise the whole version. This is why the numbers can exceed the elements you see after filtering.",
          "To focus on diagnosis, you can hide relations added by the code in Settings. Those lines describe components and codes belonging to the machine; they are not an additional witness for a cause or intervention.",
        ],
      },
      {
        id: "cercare",
        heading: "Searching a symptom or a code",
        body: [
          "Type in the search field at the top (the “/” key takes the cursor there) and choose a result. The graph highlights the diagnostic path: from the symptom or code to the causes, from the causes to the actions and components. The rest fades. “Show the whole graph” goes back to the full view.",
          "Search covers symptoms and error codes, including their alternative names, and accepts partial text. It does not search every node type. If a component name returns no results, you can explore that component in the graph and through the relations panel.",
          "For example, search for part of “pump does not start”, choose the symptom and open the line to a cause. Then follow the relation to the check or intervention and read its evidence. If there are several causes, the path highlights them without automatically choosing the correct one for a real case.",
          "Search highlights the path while keeping filters active. If part of it seems missing, return to “All” and also check the setting for relations added by the code. If you cannot find a symptom, try another term from the manual and check the selected version and PDF.",
        ],
      },
      {
        id: "prove",
        heading: "The evidence",
        body: [
          "Choosing a node or a link opens the evidence on the right: the lines of the manual with their page, the state, the witnesses that support it and, if someone decided, who. “Open page” shows the original page with the quoted text highlighted, when its position is known.",
          "The panel closes with the cross or with the Esc key.",
          "A node's details also show any alternative names and the list of connected relations. A relation's details show its two ends, overall status and occurrences. Each occurrence has its own passage and may have different witnesses, decisions and conditions.",
          "Read “Applies if”, “First”, “Warning”, “Expected result” and “Order” when shown: they clarify when the link applies and how the action should be interpreted. An expected result of a check is not a fact already observed on your machine.",
          "Page numbers follow the PDF's order, which can differ from the numbers printed in the manual. Highlighting appears only when the system knows the text's position; a page without highlighting can still be the correct source. In that case find the cited passage in the page image.",
        ],
      },
      {
        id: "dal-vivo",
        heading: "The growing graph",
        body: [
          "During an extraction the graph builds up before your eyes: new nodes appear as they are found and links change colour when they are checked. At the bottom you see the counters and the last relation found. When the extraction ends the graph opens, with the next step at the top right.",
          "Past extractions with an available recording can be replayed with “Replay the run”, at 1×, 4× or 16× speed, with pause. Replaying costs nothing: it calls no model.",
          "Counts can decrease during construction: checks can discard proposals and merging can collect several names into one node. The highest count seen during extraction is not necessarily the final amount of retained information.",
          "A replay reproduces events from an existing version. “Pause” and “Resume” control playback, not a real extraction; the cost shown belongs to the recording, not a new charge. Use it to understand the process, then open the final graph to consult its evidence and version status.",
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
          "A graph version and a PDF revision are different things: you can extract the same document several times without changing the source. A different PDF is registered as another manual. Answers on an interface version update that version; the first answer on a campaign version creates a copy instead.",
          "The current version is the newest, not necessarily the approved one or the one best suited to your consultation. Before using a path, check the version's outcome; on the manual's page you can also open earlier versions and compare them by switching between them.",
          "The “Code” column identifies the software version that produced the extraction, when available. It can help distinguish results produced at different times, but it is not a machine error code or a graph quality score.",
        ],
      },
      {
        id: "registro",
        heading: "The Runs page",
        body: [
          "It lists every run of every manual, newest first, with outcome, duration and cost. You can see only those started from the interface or only those of the evaluation campaign, and sort by column. A row leads to the right step: the graph, the questions or the run in progress.",
          "Use “From the interface” to find your work and “Campaign” to consult the reference runs already present. Clicking a sortable column heading lets you compare dates, duration or cost. The outcome helps distinguish an extraction still running, a version awaiting approval and a failed run.",
          "A dash or an empty field means a value is unavailable, not that time or cost is zero. To understand an interruption, open the row and read the run's message instead of relying only on its duration.",
        ],
      },
      {
        id: "costi",
        heading: "How the cost is made",
        body: [
          "Cost depends on model calls: page mapping, unit reads, the verifier, name review and the agent reviewing doubts, plus any additional attempts. Every call goes through the spending ledger; before it is made, the system checks that it fits within the available limits.",
          "Automatic machine identification after uploading also uses a model and may incur a small cost. Replaying a run, consulting the graph and opening available pages do not start new model calls.",
          "Applying answers reuses saved work and usually avoids repeating extraction; new checks may nevertheless have a cost. Recording approval also requires a resumed run, so the system still checks spending availability before starting.",
          "Distinguish the estimated cost in the summary from the cost recorded for a run. If a view says “Estimated cost”, do not read the value as a final charge. A low cost or short duration alone does not describe the graph's completeness or correctness.",
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
          "The schema describes the roles of elements and the meaning of their links. A symptom may indicate a cause; a code indicates a cause; the cause concerns a component and can be addressed with an action. The machine is linked to the components and codes belonging to its graph.",
          "For example, “the pump does not start”, “no power supply” and “check the cable” occupy three different roles even when they appear in the same table row. Keeping them separate allows the same cause to be linked to several symptoms or several checks to be represented for one problem.",
          "The schema is fixed for all manuals: you cannot add new types from the Ontology page. A concrete graph contains only the elements and links found for that source; it does not need to fill every possible branch of the schema. A shared schema lets you read graphs in the same way without making information about different machines identical.",
        ],
      },
      {
        id: "chi-crea",
        heading: "Who makes the links",
        body: [
          "The solid line marks links extracted by the model, each with its evidence in the manual. The dashed line marks those added by the system: they link the machine to its components and its codes.",
          "Under the schema you find the description of each kind and of each link, as written in the schema.",
          "The solid and dashed lines on this page distinguish the origin of a link. In a manual's graph, line colours also distinguish verification status. A relation allowed by the schema still needs evidence to be a verified relation in your version.",
          "Links added by the system help connect the machine to the components and codes identified. The panel labels them “Added by the system” and you can hide them in Settings; they do not replace citations for diagnostic relations.",
        ],
      },
    ],
  },
  {
    slug: "impostazioni",
    title: "Settings",
    icon: "settings",
    lead:
      "The gear at the bottom left opens Settings. Press “Save” to apply changes; “Cancel”, the cross and Esc close without saving. Extraction and review choices apply to new runs: an existing version retains them when it resumes after answers. View preferences apply to graphs after saving.",
    sections: [
      {
        id: "chiave",
        heading: "OpenAI key",
        body: [
          "Usually the key already set up on the computer is used. If you write another one, it will be used for new extractions and for reading the machine data. The key is saved locally; the interface shows only the last four characters of the key in use. “Use .env” goes back to the usual one.",
          "The key is the credential that lets the application call the OpenAI service. The field hides what you type; after saving, the interface shows only a reference to the key in use without returning its full value. The credential is used for requests to the service.",
          "Leave the field empty to keep the key already set. If you select “Use .env”, then press “Save” to confirm the return to the key configured on the computer. Without a usable key, operations requiring a model may fail; graphs already available remain accessible.",
        ],
      },
      {
        id: "estrazione",
        heading: "Extraction",
        body: [
          [
            "Reasoning: the level of processing requested from the model, from “None” to “High”. Changing it can affect time, cost and results without guaranteeing an improvement in quality.",
            "Reads per unit: how many independent readings are requested for each portion of the manual. You can choose 1, 2 or 3; the initial value is 2. A single read cannot provide the agreement witness; adding a read increases the work requested from the model.",
          ],
          "To learn the workflow, you can keep the initial values and check the result through its evidence. If you change these choices, a new extraction is needed to observe their effect: pressing “Save” does not recalculate an existing graph.",
          "Reads per unit concern relation extraction, not the number of times the PDF is uploaded. Page classification has its own process; choosing one read per unit does not remove all other checks.",
        ],
      },
      {
        id: "agente",
        heading: "Agent",
        body: [
          "The model and the reasoning of the agent that answers the doubts in your place, according to the choice made in “Who answers the doubts”.",
          "The agent is an automatic reviewer: it compares proposals with the source and can confirm, reject or leave a doubt unresolved. Changing its model affects this review; it does not replace the extraction model. For new runs the same choice is also used for review of the page map.",
          "To send doubts to the agent, choose “Agent only” or “Agent, then me” when creating the graph. With “Only me”, extraction doubts come directly to you. The saved model and reasoning do not change this choice of who answers, and final approval remains a human decision.",
        ],
      },
      {
        id: "domande",
        heading: "Questions",
        body: [
          "The most questions a person gets in one extraction. The most important come first; beyond the limit the doubts stay in the graph as unverified.",
          "The window offers 5, 10, 15 or 20 questions; the initial value is 10. The limit applies to the version as a whole and accounts for questions already presented, including after resuming. Final approval is a separate step and does not consume one of these questions.",
          "A question can contain several statements. A limit of 10 questions therefore does not mean 10 relations or guarantee that every doubt was examined. To increase the number available in a new extraction, save your choice before starting; changing the limit does not retroactively expand the questions for an existing version.",
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
          "These choices apply after “Save”, in every graph, without starting an extraction. Showing or hiding lines added by the code and node names changes only the view, not the saved nodes, evidence or decisions.",
          "If names crowd the view, turn them off and use hovering or the node panel to read them. To see at a glance which components and codes belong to the machine, turn relations added by the code back on. You can change these preferences while consulting a graph.",
        ],
      },
    ],
  },
{
  "slug": "modifica-grafo",
  "title": "Editing a graph",
  "icon": "pencil",
  "lead": "Edit graph starts a session on the version you are reading. You can correct nodes, relationships and occurrences; only final acceptance creates a new version.",
  "sections": [
    {
      "id": "percorso",
      "heading": "Edit, Check, Summary",
      "body": [
        "Edit graph is available after generation, on the open graph and in its history. The bar always identifies the base version. A running extraction or unapplied answers display the reason editing is blocked.",
        "In Edit choose Nodes, Relationships or Graph. Filters, evidence and links reach the same element across views. Edit cells, add or delete elements; Undo change and Redo change apply within this session.",
        "Next opens Check: integrity, required and optional fields, connections and sources have separate indicators. A check leads to the relevant row or field. Structural checks do not guarantee technical correctness.",
        "Next opens Summary with additions, removals and before/after values, including invalidated verification and system link updates. Back retains changes. A correction expires previous checks and acknowledgements."
      ]
    },
    {
      "id": "celle-prove",
      "heading": "Fields, relationships and evidence",
      "body": [
        "Enter commits a simple cell; Tab commits and moves to the next control; Esc cancels text in the active cell. Descriptions, instructions and lists use multiline inputs. Enter lists as JSON, for example [\"first\", \"second\"].",
        "Missing, empty, not stated and filled are different states. Zero and false count as filled. The cell menu distinguishes Clear, Set to no value and Remove optional field. IDs and unknown fields remain read-only.",
        "Relationships allow compatible endpoints only. Proposing the same triple adds an occurrence without duplicating the link. Changing endpoints or type creates a new identity. Deleting a node lists the links removed with it; deleting the last occurrence deletes the relationship.",
        "The manual’s words remain read-only. In an occurrence you can select verified source segments, conditions and a personal annotation. If the PDF or its index cannot be verified, embedded quotes remain readable; new evidence is not invented. System relationships remain read-only."
      ]
    },
    {
      "id": "accettazione",
      "heading": "Accepting a new version",
      "body": [
        "Accept changes and create new version is the only command that saves. First acknowledge the listed remaining doubts. The new version opens as accepted, with no second Approve, and the original stays unchanged. No AI calls are required.",
        "Editing a node or occurrence invalidates the affected verification. Accepting the version does not turn relationships green. After checks, Confirm content or Reject content records a human decision on the individual occurrence: human confirmation remains distinct from automatic verification, including when no source is linked.",
        "History records the parent and revision number. Download version and provenance includes the graph, frozen base, differences, checks and decision. Extraction questions remain recognisable as source context and open activities stay in Your turn.",
        "If the save result is uncertain, the session stays locked on the same content. Check save status opens the version already created or allows retrying the same request."
      ]
    },
    {
      "id": "uscita",
      "heading": "Leaving and discarding",
      "body": [
        "Changes live only in the open session. Leave without saving, the logo, breadcrumbs and sidebar ask whether to continue or discard when there are edits. Continue editing retains values; Leave and discard loses them.",
        "Reloading or closing before acceptance discards the session, including when returning with browser history. The browser may display its own exit warning. There is no autosave or draft recovery. An acceptance request already sent may still complete on the server."
      ]
    }
  ]
},
];
