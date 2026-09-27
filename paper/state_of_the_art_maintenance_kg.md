# Critical state of the art: constructing maintenance knowledge graphs from industrial manuals

**Search date:** 27 September 2026.  
**Exact publication interval:** 27 September 2016–27 September 2026, inclusive.  
**Purpose:** Related Work positioning and experimental design, not a claim of novelty or superiority.  
**Evidence set:** 20 full research papers in the main comparison; eight especially relevant published works retained separately because their full text was not successfully inspected.

## 1. Scope, interpretation and principal conclusion

The supplied architecture is treated as an **implementation description, not experimental evidence**. It combines structured reading units and segment identifiers; ontology-constrained maintenance extraction; repeated extraction and selective verification; coverage recovery; provenance-preserving consolidation; and bounded, source-grouped review. Its textual conditions are not assumed to constitute an executable diagnostic workflow. Agreement is not assumed independent, and the evidence record is not treated as a correctness certificate.

**The broad components are already established in the inspected literature.** In particular, document/layout-aware knowledge construction, ontology-guided procedural extraction, semantic canonicalization, iterative graph verification and human-assisted annotation each have substantial precedents. The most defensible initial positioning is therefore **an integrated maintenance-extraction system with a carefully tested empirical contribution**. A methodological claim needs a precisely specified algorithm or representation and evidence that it improves on these precedents, not merely a longer feature list. See [P01](#p01), [P04](#p04), [P08](#p08), [P13](#p13), [P15](#p15) and [P16](#p16).

The strongest proposed experimental focus is **source-grounded diagnostic-branch preservation at matched coverage, coupled with actual human review time at matched final quality**. This is a hypothesis about a useful research contribution, not proof of an unoccupied niche. In particular, the uninspected task-centric maintenance paper [U01](#u01), troubleshooting-tree papers [U02–U03](#u02), and procedural human-evaluation paper [U06](#u06) remain important novelty risks.

### Eligibility and access conventions

All main-set papers are English-language publications. Some use Korean, Chinese or Dutch input documents; the paper language and the evaluated input language must not be conflated. Journal articles and full research papers in refereed conference/workshop proceedings are included. None of the main entries is a review article, thesis, preprint-only work or conference abstract. P11 and P12 involve manual annotation rather than automatic KG construction; they qualify specifically because they contribute relevant document-annotation/review methods, not because a manually populated ontology alone is in scope.

“Published” follows the official article/proceedings record. Online-first publication within the interval is eligible even when a later issue/book year is assigned. Thus **P05 is an APMS 2026 paper first published online on 21 September 2026, but Springer gives its citation year as 2027**; the later print/book year is not silently substituted. P04 similarly has a 2024 issue citation and a 30 December 2023 online date.

“Full text inspected” means the methods and evaluation text could be retrieved from the linked publisher/proceedings or institutional source. It does **not** mean code was executed, data independently audited, or all scientific claims reproduced. Publisher HTML and parsed PDF text were used; PDF page screenshots were checked when available. Some PDF screenshot requests failed, so figures were not used to infer unprinted numerical values. A few extracted table values or dataset details could not be verified reliably and are explicitly marked accordingly. Access is a search-date snapshot, not a guarantee against future publisher changes or location-specific access controls. Some successful reads required an alternative retrieval route to the same primary URL.

**Not reported** means the inspected description did not provide the detail. **Not verified** means this search did not establish it, which is not evidence that the paper omits it. “No measured review time” refers to the reported study, not an assertion that its authors never measured time elsewhere. A code/data link records the artifact identified by the paper; it is not a claim of present-day reproducibility, license compatibility, or successful execution.

Primary links in Table 1 establish bibliography/access; each Table 2 row gives the precise paper section supporting its technical characterization. Paper IDs link the tables and all subsequent comparisons. Numerical scores are retained in the authors’ units and **are not ranked across incompatible datasets or evaluation units**.

## 2. Table 1 — Bibliography and access

| Paper ID | Title and authors | Year and venue | Publication type | DOI / stable ID and official publication link | Working full-text reading link and version | Publication / peer-review verification source | Relevance category |
| --- | --- | --- | --- | --- | --- | --- | --- |
| <a id="p01"></a>**P01** · [technical comparison](#p01-tech) | **Procedural Text Mining with Large Language Models**<br>Anisa Rula; Jennifer D’Souza | 2023; K-CAP 2023, pp. 9–16 | Conference research paper | [DOI: 10.1145/3587259.3627572](https://doi.org/10.1145/3587259.3627572)<br>[Official record](https://dl.acm.org/doi/10.1145/3587259.3627572) | [Read full text](https://dl.acm.org/doi/fullHtml/10.1145/3587259.3627572)<br>Published full HTML; methods and evaluation inspected | ACM full eight-page research article; [TIB institutional record](https://vivo.tib.eu/fis/display/n81464) independently identifies the published, peer-reviewed work | Direct industrial; also other procedural domains |
| <a id="p02"></a>**P02** · [technical comparison](#p02-tech) | **A Named Entity and Relationship Extraction Method from Trouble-Shooting Documents in Korean**<br>Minkyu Jeong; Hyowon Suh; Heejung Lee; Jae Hyun Lee | 2022; Applied Sciences 12(23), 11971 | Journal research article | [DOI: 10.3390/app122311971](https://doi.org/10.3390/app122311971)<br>[Official record](https://www.mdpi.com/2076-3417/12/23/11971) | [Read full text](https://www.mdpi.com/2076-3417/12/23/11971)<br>Open-access published HTML | Publisher research-article record and received/revised/accepted history | Direct industrial; Korean input, English paper |
| <a id="p03"></a>**P03** · [technical comparison](#p03-tech) | **Knowledge Graph Construction Based on a Joint Model for Equipment Maintenance**<br>Ping Lou; Dan Yu; Xuemei Jiang; Jiwei Hu; Yuhang Zeng; Chuannian Fan | 2023; Mathematics 11(17), 3748 | Journal research article | [DOI: 10.3390/math11173748](https://doi.org/10.3390/math11173748)<br>[Official record](https://www.mdpi.com/2227-7390/11/17/3748) | [Read full text](https://www.mdpi.com/2227-7390/11/17/3748)<br>Open-access published HTML | Publisher research-article record, author list and editorial history | Direct industrial; Chinese input, English paper |
| <a id="p04"></a>**P04** · [technical comparison](#p04-tech) | **Fault Knowledge Graph Construction and Platform Development for Aircraft PHM**<br>Xiangzhen Meng; Bo Jing; Shenglong Wang; Jinxin Pan; Yifeng Huang; Xiaoxuan Jiao | 2024; Sensors 24(1), 231; first online 30 December 2023 | Journal research article | [DOI: 10.3390/s24010231](https://doi.org/10.3390/s24010231)<br>[Official record](https://www.mdpi.com/1424-8220/24/1/231) | [Read full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC10781358/)<br>Published open-access article in PMC; not a preprint | Publisher received/revised/accepted record; [PubMed publication record](https://pubmed.ncbi.nlm.nih.gov/38203092/) matches authors, DOI and PMC copy | Direct industrial; downstream platform |
| <a id="p05"></a>**P05** · [technical comparison](#p05-tech) | **FlowExtract: Procedural Knowledge Extraction from Maintenance Flowcharts**<br>Guillermo Gil de Avalle; Laura Maruster; Eric Sloot; Christos Emmanouilidis | 2027; APMS 2026; IFIP AICT 808, pp. 354–369; first online 21 September 2026; publisher citation year 2027 | Conference research paper | [DOI: 10.1007/978-3-032-38594-9_24](https://doi.org/10.1007/978-3-032-38594-9_24)<br>[Official record](https://link.springer.com/chapter/10.1007/978-3-032-38594-9_24) | [Read full text](https://link.springer.com/chapter/10.1007/978-3-032-38594-9_24)<br>Published chapter HTML with methods and results retrievable; online-first version | [Official proceedings description](https://link.springer.com/book/10.1007/978-3-032-38594-9) explicitly says refereed proceedings and 269 full papers selected from 320 submissions | Direct industrial refurbishment; Dutch input, English paper |
| <a id="p06"></a>**P06** · [technical comparison](#p06-tech) | **Towards Efficient Field Service Engineering for Powertrains via LLM-generated Knowledge Graphs**<br>Prerna Juhlin; Rana Hussein; Nicolai Schoch | 2025; SKGi 2025, CEUR Workshop Proceedings 4064; eight-page paper | Peer-reviewed workshop research paper | Stable ID: Vol-4064/SKGi-paper2<br>[Official record](https://ceur-ws.org/Vol-4064/) | [Read full text](https://ceur-ws.org/Vol-4064/SKGi-paper2.pdf)<br>Official published proceedings PDF; stable ID Vol-4064/SKGi-paper2 | [Workshop preface](https://ceur-ws.org/Vol-4064/SKGI-preface.pdf): single-blind review, at least two researchers per paper; seven submissions, two rejected | Direct industrial; downstream field service |
| <a id="p07"></a>**P07** · [technical comparison](#p07-tech) | **Knowledge Graph Construction towards a Graph RAG-Enhanced Intelligent Maintenance Chatbot**<br>Hansi Zhang; Wilma Johanna Schmidt; Xiaozhi Shen; Qiushi Cao; Sebastian Monka; Adrian Paschke | 2025; SKGi 2025, CEUR Workshop Proceedings 4064; seven-page paper | Peer-reviewed workshop research paper | Stable ID: Vol-4064/SKGi-paper3<br>[Official record](https://ceur-ws.org/Vol-4064/) | [Read full text](https://ceur-ws.org/Vol-4064/SKGi-paper3.pdf)<br>Official published proceedings PDF; stable ID Vol-4064/SKGi-paper3 | [Workshop preface](https://ceur-ws.org/Vol-4064/SKGI-preface.pdf) explicitly documents single-blind peer review; official volume identifies this full paper | Direct industrial; downstream chatbot architecture |
| <a id="p08"></a>**P08** · [technical comparison](#p08-tech) | **Ontology-guided Knowledge Graph Construction from Maintenance Short Texts**<br>Zeno van Cauter; Nikolay Yakovets | 2024; KaLLM 2024, pp. 75–84 | Peer-reviewed workshop research paper | [DOI: 10.18653/v1/2024.kallm-1.8](https://doi.org/10.18653/v1/2024.kallm-1.8)<br>[Official record](https://aclanthology.org/2024.kallm-1.8/) | [Read full text](https://aclanthology.org/2024.kallm-1.8.pdf)<br>Official published proceedings PDF | ACL article record and [proceedings preface](https://aclanthology.org/2024.kallm-1.0.pdf): archival submissions assessed using reviewer recommendations; full ten-page paper | Direct industrial; maintenance short texts, not manuals |
| <a id="p09"></a>**P09** · [technical comparison](#p09-tech) | **MyFixit: An Annotated Dataset, Annotation Tool, and Baseline Methods for Information Extraction from Repair Manuals**<br>Nima Nabizadeh; Dorothea Kolossa; Martin Heckmann | 2020; LREC 2020, pp. 2120–2128 | Conference research paper | Stable ID: 2020.lrec-1.260<br>[Official record](https://aclanthology.org/2020.lrec-1.260/) | [Read full text](https://aclanthology.org/2020.lrec-1.260.pdf)<br>Official published proceedings PDF; stable Anthology ID 2020.lrec-1.260 | Official LREC research proceedings record and complete nine-page paper; no DOI asserted | Transferable method; consumer-device repair manuals |
| <a id="p10"></a>**P10** · [technical comparison](#p10-tech) | **MaintIE: A Fine-Grained Annotation Schema and Benchmark for Information Extraction from Maintenance Short Texts**<br>Tyler K. Bikaun; Tim French; Michael Stewart; Wei Liu; Melinda Hodkiewicz | 2024; LREC-COLING 2024, pp. 10939–10951 | Conference research paper | Stable ID: 2024.lrec-main.954<br>[Official record](https://aclanthology.org/2024.lrec-main.954/) | [Read full text](https://aclanthology.org/2024.lrec-main.954.pdf)<br>Official published proceedings PDF; stable Anthology ID 2024.lrec-main.954 | Official LREC-COLING research proceedings record and complete research paper; stable ID used instead of an unverified DOI | Direct industrial; maintenance short texts |
| <a id="p11"></a>**P11** · [technical comparison](#p11-tech) | **Annotation and Extraction of Industrial Procedural Knowledge from Textual Documents**<br>Anisa Rula; Gloria Re Calegari; Antonia Azzini; Ilaria Baroni; Irene Celino | 2023; K-CAP 2023; eight-page paper | Conference research paper | [DOI: 10.1145/3587259.3627570](https://doi.org/10.1145/3587259.3627570)<br>[Official record](https://dl.acm.org/doi/10.1145/3587259.3627570) | [Read full text](https://dl.acm.org/doi/fullHtml/10.1145/3587259.3627570)<br>Published full HTML | ACM K-CAP full research article with methods and user-study results; distinct DOI and study from P01 | Direct industrial review/annotation method; manual KG authoring |
| <a id="p12"></a>**P12** · [technical comparison](#p12-tech) | **Agreement Behavior of Isolated Annotators for Maintenance Work-Order Data Mining**<br>Emily M. Hastings; Thurston Sexton; Michael P. Brundage; Melinda Hodkiewicz | 2019; Annual Conference of the PHM Society 11(1) | Conference technical research paper | [DOI: 10.36001/phmconf.2019.v11i1.791](https://doi.org/10.36001/phmconf.2019.v11i1.791)<br>[Official record](https://papers.phmsociety.org/index.php/phmconf/article/view/791) | [Read full text](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=928113)<br>NIST-hosted conference manuscript; title, authors, 2019 conference footer and open license match the published record | Official proceedings classifies this as “Technical Research Papers”; [NIST publication record](https://www.nist.gov/publications/agreement-behavior-isolated-annotators-maintenance-work-order-data-mining) corroborates the publication | Direct industrial; annotation and alias review, not automatic KG extraction |
| <a id="p13"></a>**P13** · [technical comparison](#p13-tech) | **Fonduer: Knowledge Base Construction from Richly Formatted Data**<br>Sen Wu; Luke Hsiao; Xiao Cheng; Braden Hancock; Theodoros Rekatsinas; Philip Levis; Christopher Ré | 2018; SIGMOD 2018; sixteen-page paper | Conference research paper | [DOI: 10.1145/3183713.3183729](https://doi.org/10.1145/3183713.3183729)<br>[Official record](https://dl.acm.org/doi/10.1145/3183713.3183729) | [Read full text](https://sing.stanford.edu/site/assets/publications/fonduer-sigmod18.pdf)<br>Stanford-hosted author-formatted accepted manuscript with ACM publication metadata; not labelled publisher VoR | ACM SIGMOD publication identified by exact DOI; institutional PDF first page gives matching authors, title, SIGMOD event, ISBN and ACM copyright | Transferable method; includes industrial electronics datasheets |
| <a id="p14"></a>**P14** · [technical comparison](#p14-tech) | **PubTables-1M: Towards Comprehensive Table Extraction From Unstructured Documents**<br>Brandon Smock; Rohith Pesala; Robin Abraham | 2022; IEEE/CVF CVPR 2022, pp. 4634–4642 | Conference research paper | [DOI: 10.1109/CVPR52688.2022.00459](https://doi.org/10.1109/CVPR52688.2022.00459)<br>[Official record](https://openaccess.thecvf.com/content/CVPR2022/html/Smock_PubTables-1M_Towards_Comprehensive_Table_Extraction_From_Unstructured_Documents_CVPR_2022_paper.html) | [Read full text](https://openaccess.thecvf.com/content/CVPR2022/papers/Smock_PubTables-1M_Towards_Comprehensive_Table_Extraction_From_Unstructured_Documents_CVPR_2022_paper.pdf)<br>Official published CVF proceedings PDF | Official CVPR open-access research-paper record; [IEEE record](https://ieeexplore.ieee.org/document/9879666/) supplies publication DOI | Transferable method; table structure and headers |
| <a id="p15"></a>**P15** · [technical comparison](#p15-tech) | **PiVe: Prompting with Iterative Verification Improving Graph-based Generative Capability of LLMs**<br>Jiuzhou Han; Nigel Collier; Wray Buntine; Ehsan Shareghi | 2024; Findings of ACL 2024, pp. 6702–6718 | Peer-reviewed conference Findings research paper | [DOI: 10.18653/v1/2024.findings-acl.400](https://doi.org/10.18653/v1/2024.findings-acl.400)<br>[Official record](https://aclanthology.org/2024.findings-acl.400/) | [Read full text](https://aclanthology.org/2024.findings-acl.400.pdf)<br>Official published proceedings PDF | ACL article record and [Findings proceedings](https://aclanthology.org/2024.findings-acl.0/); not an arXiv-only submission | Transferable method; iterative graph verification |
| <a id="p16"></a>**P16** · [technical comparison](#p16-tech) | **Extract, Define, Canonicalize: An LLM-based Framework for Knowledge Graph Construction**<br>Bowen Zhang; Harold Soh | 2024; EMNLP 2024, pp. 9820–9836 | Conference research paper | [DOI: 10.18653/v1/2024.emnlp-main.548](https://doi.org/10.18653/v1/2024.emnlp-main.548)<br>[Official record](https://aclanthology.org/2024.emnlp-main.548/) | [Read full text](https://aclanthology.org/2024.emnlp-main.548.pdf)<br>Official published proceedings PDF | ACL EMNLP main-conference research record, complete paper and publisher BibTeX | Transferable method; extraction and schema canonicalization |
| <a id="p17"></a>**P17** · [technical comparison](#p17-tech) | **DREEAM: Guiding Attention with Evidence for Improving Document-Level Relation Extraction**<br>Youmi Ma; An Wang; Naoaki Okazaki | 2023; EACL 2023, pp. 1971–1983 | Conference research paper | [DOI: 10.18653/v1/2023.eacl-main.145](https://doi.org/10.18653/v1/2023.eacl-main.145)<br>[Official record](https://aclanthology.org/2023.eacl-main.145/) | [Read full text](https://aclanthology.org/2023.eacl-main.145.pdf)<br>Official published proceedings PDF | ACL EACL main-conference research record and complete paper | Transferable method; relation extraction with evidence sentences |
| <a id="p18"></a>**P18** · [technical comparison](#p18-tech) | **WiCE: Real-World Entailment for Claims in Wikipedia**<br>Ryo Kamoi; Tanya Goyal; Juan Diego Rodriguez; Greg Durrett | 2023; EMNLP 2023, pp. 7561–7583 | Conference research paper | [DOI: 10.18653/v1/2023.emnlp-main.470](https://doi.org/10.18653/v1/2023.emnlp-main.470)<br>[Official record](https://aclanthology.org/2023.emnlp-main.470/) | [Read full text](https://aclanthology.org/2023.emnlp-main.470.pdf)<br>Official published proceedings PDF | ACL EMNLP main-conference research record and complete paper | Transferable method; source entailment and evidence retrieval |
| <a id="p19"></a>**P19** · [technical comparison](#p19-tech) | **SelfCheckGPT: Zero-Resource Black-Box Hallucination Detection for Generative Large Language Models**<br>Potsawee Manakul; Adian Liusie; Mark Gales | 2023; EMNLP 2023, pp. 9004–9017 | Conference research paper | [DOI: 10.18653/v1/2023.emnlp-main.557](https://doi.org/10.18653/v1/2023.emnlp-main.557)<br>[Official record](https://aclanthology.org/2023.emnlp-main.557/) | [Read full text](https://aclanthology.org/2023.emnlp-main.557.pdf)<br>Official published proceedings PDF | ACL EMNLP main-conference research record and complete paper | Transferable method; sampling-based consistency checks |
| <a id="p20"></a>**P20** · [technical comparison](#p20-tech) | **CoAnnotating: Uncertainty-Guided Work Allocation between Human and Large Language Models for Data Annotation**<br>Minzhi Li; Taiwei Shi; Caleb Ziems; Min-Yen Kan; Nancy Chen; Zhengyuan Liu; Diyi Yang | 2023; EMNLP 2023, pp. 1487–1505 | Conference research paper | [DOI: 10.18653/v1/2023.emnlp-main.92](https://doi.org/10.18653/v1/2023.emnlp-main.92)<br>[Official record](https://aclanthology.org/2023.emnlp-main.92/) | [Read full text](https://aclanthology.org/2023.emnlp-main.92.pdf)<br>Official published proceedings PDF | ACL EMNLP main-conference research record and complete paper | Transferable method; selective human/LLM annotation |

## 3. Table 2 — Technical comparison

The “claimed contribution” column paraphrases the authors’ positioning. It is deliberately separate from measured findings. For all rows, an absence of a listed chain/citation/time result must not be replaced by a downstream benefit claimed in an abstract.

| Paper ID | Problem and industrial domain | Input documents/data and output representation | Main method and pipeline stages | Authors’ claimed contribution / innovation | Shared features and important differences | Evaluation: size, annotation, splits, baselines, metrics | Main measured findings | Limitations, review/transfer evidence and available artifacts | Supporting section, table or page |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| <a id="p01-tech"></a>[**P01**](#p01) | Procedures in manufacturing and three other domains. | Selected PDF procedures → automatically generated text and ontology instances in Turtle. | GPT-4 plus PDF plugin; incremental list/count/sequence/nesting questions; ontology definitions and two-shot examples. | LLM-based procedural extraction with ontology-guided in-context learning. | Shares supplied ontology, steps/substeps and PDF context. No stable segment-ID evidence reconstruction or tested selective review. | Four domains; approximately 3–4 procedures/domain, chosen to be enumerated and ≤2 pages. Human references; raw/definition/two-shot comparisons. ROUGE, not graph-semantic matching; no manufacturer holdout. | Manufacturing ontology ROUGE-1: 59.0→78.9 on the zero-/two-shot example. Reports cross-column procedure mixing and invented steps. | Pilot selection and serialization-sensitive scores; no measured review time. [Prompts/data](https://github.com/jd-coderepos/proc-tm/). Direct challenge to procedural-LLM novelty; source/chain accuracy not separately quantified. | §§3–6; Tables 1–2; §6 qualitative observations 6–9. |
| <a id="p02-tech"></a>[**P02**](#p02) | Plant troubleshooting information extraction. | Korean failure/repair tables → typed entities and relation sets; not a demonstrated executable workflow. | Manual cleaning; expert BIO labels; KLUE NER and dependency parsing; ten relation rules. | Domain entity extraction plus grammar-based relation rules for troubleshooting. | Shares component/failure/action extraction. Relies on Korean linguistic processing; no LLM, repeated extraction or evidence audit trail. | 900 sentences: 451 failure, 449 repair, from 10 equipment documents after filtering. Random 70/30 split; CRF and two morphological analyzers as comparisons. | Best NER F1: 0.8235 failure / 0.6888 repair. Table 10: 133/179 completely correct sentences and 163/186 correct relation sets; distinct denominators. | The 179-sentence relation subset is not interchangeable with the full test split. No source-citation, chain, transfer or timed-review evaluation. Code/data release not verified. | §§3–7; Tables 9–10. |
| <a id="p03-tech"></a>[**P03**](#p03) | Textile-equipment maintenance; warping-machine case. | Chinese manuals, reports and standards → automatically extracted and consolidated Neo4j KG. | Expert ontology; enhanced BERT–BiLSTM–CRF joint extraction; lexical/embedding duplicate matching; graph queries. | Joint extraction intended to reduce cascading errors in an equipment-maintenance KG. | Shares ontology, entity fusion and procedural links including first/next step. Duplicate removal does not establish occurrence-preserving provenance. | 8:1:1 split; total corpus size not verified. Comparisons include pipeline and sequence-model baselines; extraction precision/recall/F1. | Reported joint-model F1: 0.847. The inspected evaluation does not separately establish complete diagnostic-branch correctness. | One industrial setting; no held-out manufacturer test, citation-accuracy assessment or measured review time. Matching threshold is task-specific. Code/data release not verified. | §3; §4.2 Table 3; §4.3 Tables 4–5; §4.4. |
| <a id="p04-tech"></a>[**P04**](#p04) | Aircraft flight-control fault knowledge. | Chinese manual and fault cases for one aircraft type → supervised extraction plus human-audited KG. | ERNIE-RCNN text routing; ERNIE–BiLSTM–CRF–TreeBiLSTM joint extraction; fusion, audit interface, Neo4j and QA. | Reduce text complexity and extraction error propagation; integrate a fault-KG platform. | Shares source-linked extraction and expert correction: sentence IDs, original text/entity positions and source highlighting. Not the proposed budgeted grouped-review protocol. | 1,000 fault texts, 1,648 entities; 700/300 training/test; five runs. Joint extraction compared with CasRel/GPLinker using exact triples. | 94.75% is text-classification accuracy, NOT relation accuracy. A reliably transcribed joint-extraction numerical result is not provided here. | Automatic and manual construction mixed. No separately measured citation entailment, complete chains, human review time or cross-aircraft transfer. Code/data release not verified. | §§2–4, especially §§4.1/4.3 and Table 6; §§5.3–5.4 audit/platform. |
| <a id="p05-tech"></a>[**P05**](#p05) | Industrial refurbishment troubleshooting flowcharts. | 35 Dutch digital flowcharts → automatically detected nodes, directed edges, branch labels and JSON/RDF-compatible structure. | YOLOv8s, OCR and geometric arrow analysis reconstruct flow and yes/no connections. | Combine learned element detection with geometric reconstruction of procedural graphs. | Directly represents branch topology; current architecture mainly keeps textual conditions. Diagram extraction is a different input task from table/prose extraction. | 25/3/7 chart train/validation/test split; 1,145 elements plus 62 branch labels. Node, edge and label metrics; VLM comparison has differing matching assumptions. | Node F1 98.8%; edge precision 85.5%, recall 54.6%, F1 66.7. Strong nodes do not imply complete paths. | Single manufacturer; digitally created charts; cross-page connectors and broad transfer not established. No timed review/source-entailment study. [Code](https://github.com/aixpert-rug/FlowExtract). | §§3–5; Tables 1–3. Bibliographic year exception explained in Table 1. |
| <a id="p06-tech"></a>[**P06**](#p06) | ABB powertrain field service. | Drive/service manuals plus structured enterprise information → mixed extracted and database-linked KG. | GPT-4; LangChain graph transformer and Microsoft GraphRAG comparison; schema/domain prompts; code preservation and expert inspection. | An industrial KG workflow intended to support efficient service engineering. | Shares ontology guidance, full repair instructions and review. Ten repeated runs examine variability, not statistically independent evidence of correctness. | Node/relation counts across ten runs and qualitative error assessment. Manual corpus size and reproducible gold-standard protocol not reported. | Out-of-schema content, missing entities and wrong associations persist. Reported hallucination percentages lack a sufficiently explicit denominator for use as extraction precision. | No defensible complete-chain/source-citation metric, timed human review or manufacturer transfer. Code/data release not verified. Strong systems-level novelty challenge. | §§3.1–3.4; Table 1 and discussion. |
| <a id="p07-tech"></a>[**P07**](#p07) | Bosch manufacturing maintenance chatbot infrastructure. | 49 heterogeneous documents from five stations on one line → extracted, human-annotated and consolidated KG. | Maintenance ontology; GPT-4 terminology processing; OneKE extraction; dictionaries/regex; human annotation and mapping/deduplication. | Domain KG foundation for a GraphRAG maintenance assistant. | Shares ontology, procedures, document linkage and human curation. Mostly Chinese mixed-format records, not a PDF-manual-only pipeline. | Graph statistics and two ontology Likert questions answered by four data scientists. No extraction gold set, train/test protocol or quantitative QA comparison. | 21,893 triples, 4,461 subjects and 9,337 objects. These are size counts, not correctness scores; quantitative chatbot evaluation remains future work. | No measured review-time benefit, chain preservation or grounded-edge precision. Domain ontology/system contribution, not demonstrated downstream superiority. Code/data release not verified. | §§2.1–3; Tables 1–2; §4 future evaluation. |
| <a id="p08-tech"></a>[**P08**](#p08) | Maintenance short-text fact extraction. | MaintIE work-order sentences → automatically generated ontology-guided triples. | Semantically retrieve demonstrations; prompt Llama-2/3 with ontology entities/relations; no model fine-tuning. | Inference-only domain extraction with relatively few in-context examples. | Shares supplied schema and extraction prompts. Domain/range constraints omitted from prompts; no PDF structure, occurrence provenance or branch repair. | 6,728 usable records after removing 272 empty-triple records; 5,046/1,682 split. Exact triple F1; conformance and lexical hallucination proxies; shot/model comparisons. | Llama-3-70B F1 about 0.69 with 20 examples and 0.77 with 150. This is not a source-entailment score. | Filtering and benchmark-specific split prevent direct score comparisons with P10. No manufacturer holdout or measured review time. [Code/benchmark](https://github.com/zeno17/MaintIE2KGBench). | §§3–5; Tables 1–2. |
| <a id="p09-tech"></a>[**P09**](#p09) | Consumer-device disassembly/repair instructions. | iFixit semi-structured guides → automatic tool, part and removal-verb labels; not a full KG. | Toolbox-based n-gram matching; Flair/BiLSTM-CRF sequence labeling; semi-automatic checkbox annotation. | Repair dataset, word/step annotation schemes and practical IE baselines. | Shares steps, contextual references and assisted review. Input already structured; implicit step-level information exceeds word-span extraction. | 31,601 guides collected; 1,497 Mac-laptop guides annotated via 4,350 unique step texts. Random 80/10/10; duplicate-safe split grouping not verified. | Tool exact-set accuracy 94.3% on all annotated data; held-out part F1 0.88 and verb F1 0.95. Different tasks/denominators. | Implicit step annotations excluded from part evaluation; review speedup claimed but not timed. No diagnostic chains/transfer. [Dataset](https://github.com/rub-ksv/MyFixit-Dataset), [annotator](https://github.com/rub-ksv/MyFixit-Annotator). | §§2–5; Tables 1–3. |
| <a id="p10-tech"></a>[**P10**](#p10) | Fine-grained maintenance information extraction. | Work-order short texts → human gold entities/relations and supervised extraction benchmarks. | Hierarchical schema; expert annotation/adjudication; coarse preannotation; SpERT/REBEL experiments. | A fine-grained benchmark and evidence on schema granularity and transfer from coarse labels. | Shares typed maintenance relations and reviewer corrections, but not PDF layout or evidence-grounded extraction. | Abstract/Table 2: 1,076 fine + 7,000 coarse texts; §6.1 says 1,067 fine. Random 80/10/10; retain fully agreed fine annotations. Strict/loose metrics. | At 224 classes, fine-trained SpERT strict relation micro-F1 27.3 versus loose 55.7. Reported annotation work: about 60 h fine / 40 h coarse. | Granularity/workflows differ: annotation totals are not a controlled speedup. Agreement filtering may omit difficult cases; no manufacturer transfer or citation metric. [Data/code](https://github.com/nlp-tlp/maintie). | §§5–8; Tables 2 and 4; preserve the paper’s count discrepancy. |
| <a id="p11-tech"></a>[**P11**](#p11) | Industrial procedural annotation and review. | PDF text/regions → manually authored ontology instances and RDF export. | ONTO-PAWLS: ontology-configured labels/relations, document-region selection and procedural representation. | Integrate semantic annotation with native-document procedural knowledge capture. | Shares source-based human interaction, ontology constraints and step/subplan relations. Extraction is human annotation/export, not automated LLM content extraction. | 11 students/researchers annotate a procedure and answer usability questions. One task; no randomized comparison against another interface. | Mean completion time 13 minutes, range 6–24. Actual task time was measured, but a review-time reduction was not established. | Not a technician/manufacturer transfer study; no automatic extraction, citation-accuracy or whole-chain benchmark. Software described; exact independently usable release not verified. | §§3–6, especially tool workflow and user evaluation. |
| <a id="p12-tech"></a>[**P12**](#p12) | Excavation-machine maintenance work-order annotation. | MWO tokens → human-assigned aliases and Item/Problem/Solution/Unknown categories, not automatic KG triples. | Nestor TF-IDF prioritization, fuzzy suggestions and time-stamped expert tagging. | Empirically examine isolated annotator agreement and deployment implications. | Shares normalization, ambiguous categories and prioritized review. Human consensus is measured; no budgeted relation-question grouping. | Six experts, approximately 30-minute sessions; public excavation data; raw MWO count not reported in the study description. Fleiss’ kappa and progress over time. | Mean 265 annotations/person (175–357); alias kappa 0.85 and category kappa 0.66. | No independent truth labels or quality-matched baseline. Collaborative feedback is proposed, not tested. No chain/citation/transfer study. [Nestor](https://github.com/usnistgov/nestor). | §1.2; §§2–4; Figures 2–4. |
| <a id="p13-tech"></a>[**P13**](#p13) | Richly formatted knowledge extraction, including electronics datasheets. | PDF/HTML/XML → automatically populated relational KB using human weak supervision. | Document hierarchy with table/cell/page/box context; candidate matchers/throttlers; multimodal BiLSTM; labeling functions and probabilistic classification. | Unified multimodal, document-level KBC with weak-supervision programming. | Strong precedent for structural context, source pointers, pruning and human involvement. Not maintenance branches or claim-level evidence verification. | Four domains; electronics: 7,000 PDFs, over 20 manufacturers. Oracle text/table/ensemble baselines; feature ablations. Gold split details not verified. User study: eight analyzed after two outliers. | Electronics F1 0.77 versus ensemble upper-bound 0.42. Thirty-minute development study: mean F1 0.49 with labeling functions versus 0.26 manual labeling. | Development supervision time, not post-extraction review time. Multiple domains tested separately, not held-out transfer. Public release status not independently verified here. | §§3–6; Tables 1–4; §6 user study. |
| <a id="p14-tech"></a>[**P14**](#p14) | Table detection, structure recognition and functional analysis. | Scientific-article PDF/XML → aligned and canonicalized table annotations; automatically predicted cells/headers. | Character alignment; header/spanning-cell canonicalization; quality filtering; DETR versus Faster R-CNN. | Large, more consistent table ground truth and comprehensive extraction baseline. | Shares merged-cell/header concerns and structural checking. No maintenance ontology or semantic relation extraction. | 947,642 tables; document-level 80/10/10 split: 758,849/94,959/93,834. Canonical/noncanonical comparisons; AP, exact content accuracy and GriTS. | DETR exact table-content accuracy 0.8138 overall; complex-table accuracy 0.6944 versus 0.5360 for noncanonical training/evaluation. | Single-page tables only; quality filtering and domain-specific canonicalization limit transfer. Structural correctness is not diagnostic correctness; no human review-time test. [Code/data](https://github.com/microsoft/table-transformer). | §§3–5; Tables 4–5. |
| <a id="p15-tech"></a>[**P15**](#p15) | General-domain text-to-graph generation. | Text/reference-graph corpora → LLM-generated and iteratively corrected graphs. | Perturb seed graphs; train T5/Flan-T5 verifier; re-prompt generator or append corrections offline, up to three iterations. | Fine-grained verifier feedback improves graph generation and dataset augmentation. | Direct precedent for a second-stage verifier and missing-triple recovery. Not two independent extractor calls; verifier is learned and fallible. | KELM-sub 60,000/1,800/1,800; WebNLG; GenWiki 1,000 human-gold test pairs. Base/self-refinement comparisons; triple/graph F1, semantic matching, GED and runtime. | KELM unified verifier: triple F1 13.50→23.11; exact-graph F1 4.89→7.50. Different evaluation units. | WebNLG-trained verifier tested on GenWiki, not industrial transfer. No measured human review time or citation audit. Synthetic/reference graphs need not equal strict source entailment. [Code/data](https://github.com/Jiuzhouh/PiVe). | §§3–5; Tables 1–4; §4.8 costs. |
| <a id="p16-tech"></a>[**P16**](#p16) | Open/schema-constrained KG construction. | Natural-language benchmark text → extracted and canonicalized triples. | Open extraction; define relation meaning; embedding retrieval plus LLM schema alignment; optional refinement. | Separate extraction from schema canonicalization without requiring extraction-time schema conditioning. | Shares semantic normalization. Mainly relation/schema canonicalization, not proof of entity-identity resolution or provenance-preserving occurrence merging. | WebNLG (1,165), REBEL (1,000 sampled) and Wiki-NRE; latter count not verified. GPT/Mistral variants; published supervised and canonicalization comparisons; strict/partial/semantic metrics. | Refinement generally improves the reported partial-matching results. Target-schema mode can discard triples lacking an equivalent relation. | Discarding improves conformance without proving coverage. No industrial branch/citation or actual review-time evaluation. [Code](https://github.com/clear-nus/edc). | §§3–4; Figure 2; Tables 1–2 and appendices. |
| <a id="p17-tech"></a>[**P17**](#p17) | Document-level relation and evidence extraction. | DocRED/Re-DocRED with entity mentions → predicted relations and supporting sentence sets. | Evidence-supervised attention; teacher/student learning; pseudo-evidence and inference-stage document rescoring. | Improve relation extraction by explicitly learning evidence relevance. | Shares relation-level source support; assumes entity annotations and does not process PDF layout. Evidence selection is not a correctness certificate. | Supervised and distantly supervised settings; ATLOP/EIDER/SAIS/KD-DocRE comparisons. Exact dataset counts not reverified here; relation F1 and evidence F1 separately reported. | RoBERTa-large student/fusion relation test F1 67.53; evidence F1 57.34. Relation quality and evidence quality differ. | No complete maintenance-chain, manufacturer transfer or measured review-time results. Re-DocRED evidence limitations discussed. [Code](https://github.com/YoumiMa/dreeam). | §§3–4; Tables 1–5. |
| <a id="p18-tech"></a>[**P18**](#p18) | Check whether a cited document supports a claim. | Wikipedia claims plus external cited articles → supported/partial/unsupported labels and evidence sentences; no KG construction. | Split claims; crowd annotation; retrieval and NLI baselines; supervised and prompted models. | Realistic evidence-grounded entailment benchmark with subclaim analysis. | Direct model for testing edge-plus-condition support, distinct from mere citation existence. | Claims: 1,260/349/358 train/dev/test; subclaims: 3,470/949/958. Human judgments; model and oracle-evidence comparisons. | Off-the-shelf T5-3B ANLI claim F1 64.3 versus human 83.3; subclaim scores differ. Do not treat subclaim success as full-claim support. | Non-industrial, no layout/branch or time-saving experiment. Operational safety/causal truth is beyond source entailment. [Data/code](https://github.com/ryokamoi/wice). | §§2–3; Tables 1–5; dataset appendix. |
| <a id="p19-tech"></a>[**P19**](#p19) | Sampling-based hallucination detection. | Generated biographies and alternative samples → sentence/passage risk scores; no source-extracted KG. | Compare sampled outputs using lexical, semantic, QA, NLI or prompted consistency checks. | Black-box factuality estimation without accessing model probabilities. | Precedent for agreement signals. Does not establish independence or justify treating agreement between two calls as correctness. | 238 passages, 1,908 annotated sentences; 20 stochastic samples per passage. AUC-PR and passage correlations; random/grey-box comparisons. | Sampling-based checks outperform several evaluated uncertainty baselines; no two-call maintenance result established. A single comparable numerical result is not reproduced here. | Agreement can preserve shared errors; no explicit manual-source grounding, branch evaluation or measured review time. No industrial transfer. [Code/data](https://github.com/potsawee/selfcheckgpt). | §§3–7; Tables 1–2; Limitations. |
| <a id="p20-tech"></a>[**P20**](#p20) | Allocate text-labeling work between people and LLMs. | Six classification/semantic datasets → hybrid annotation sets and downstream classifiers, not a KG. | Repeated-prompt entropy ranks cases for human/LLM assignment; aggregate labels; compare random allocation. | Uncertainty-guided allocation improves annotation cost/quality trade-offs. | Shares selective review and repeated sampling. Human labels are dataset labels, not a new timed maintenance-review experiment. | Six tasks including AG News, TREC and TempoWiC; roughly 1,000 training examples when subsampling; held-out downstream macro-F1 across allocation fractions. | TempoWiC at 40% LLM allocation: different-prompt entropy 56.9 versus random 53.2 macro-F1. | Financial savings use modeled annotation costs, not observed reviewer minutes. No grouped source questions/diagnostic chains or industrial transfer. [Code](https://github.com/SALT-NLP/CoAnnotating). | §§3–5; Table 2; §4.3 cost model; limitations. |

## 4. Ranked shortlist: the ten most serious inspected comparisons

This ranking concerns **relevance to the proposed contribution**, not venue prestige or numerical performance. The access-limited works in §8 are not silently treated as inspected comparisons.

1. **[P01 — Procedural Text Mining](#p01).** Closest to ontology-guided LLM extraction of steps and substeps from manuals. Its documented procedure-mixing errors make branch preservation an especially important comparative target.
2. **[P13 — Fonduer](#p13).** The strongest early challenge to structural-context novelty. It also establishes a higher evidential bar for an efficiency argument than simply reporting a user-friendly interface.
3. **[P06 — ABB powertrain KG construction](#p06).** Close industrial systems comparison for extracting service knowledge with LLMs. Its variability/error analysis makes repeatability and semantic correctness worth separating experimentally.
4. **[P04 — Aircraft PHM KG platform](#p04).** Important counterexample to claiming that source-linked extraction plus an expert auditing interface is new. Compare the granularity and verified quality of provenance, not its mere presence.
5. **[P08 — Ontology-guided maintenance extraction](#p08).** A particularly practical published LLM baseline. Its benchmark setting also forces a clear explanation of why full manuals are harder than maintenance short texts.
6. **[P07 — Bosch maintenance KG](#p07).** Close ontology/extraction/curation integration. An evaluated extraction-and-review contribution could be differentiated from its reported evidence, but not by omitting this related system.
7. **[P05 — FlowExtract](#p05).** A direct procedural-topology comparison on an appropriate diagram subset. It shows why detecting components and reconstructing correct diagnostic paths require separate evaluation.
8. **[P03 — Joint equipment-maintenance extraction](#p03).** A non-LLM industrial baseline family covering extraction and fusion. Relevant to distinguishing source-aware consolidation from conventional deduplication.
9. **[P02 — Troubleshooting document extraction](#p02).** A useful rule/supervised counterweight to LLM-only baselines. Adapt its principles to the target language while clearly labeling the result an adaptation, not a reproduced score.
10. **[P11 — ONTO-PAWLS procedural annotation](#p11).** A direct review-interface comparator. Its human study is a reason to measure comparable work, not to equate annotation/export with automatic extraction.

For particular experiments, [P15](#p15) is the strongest verification-method comparator, [P16](#p16) the schema-canonicalization comparator, and [P10](#p10)/[P12](#p12)/[P20](#p20) important annotation-design references. These are not displaced scientifically by their absence from the domain-focused top ten.

## 5. Synthesis: established capabilities and cautiously framed gaps

### 5.1 What should not be claimed as new

**Layout and document context are established concerns, not a newly discovered problem.** The inspected work covers richly formatted knowledge construction and table canonicalization. The defensible question is whether the proposed document representation preserves *maintenance-specific branch membership and evidence* better under realistic extraction errors. A generic “we preserve layout” claim is insufficient. [P13](#p13), [P14](#p14)

**Ontology-constrained maintenance/procedural extraction also has direct predecessors.** The contribution cannot rest on representing components, faults and actions, supplying an ontology to a model, or recording sequential relations. A useful comparison should instead distinguish successful serialization from semantically correct, complete and source-supported diagnostic structures. [P01](#p01), [P02](#p02), [P03](#p03), [P08](#p08)

**Verification, normalization and human involvement are established building blocks.** Iterative graph correction, sample-based consistency checks, schema canonicalization and human semantic annotation are already studied. A second call, an entailment prompt, a deduplication pass or an approval screen is not automatically a methodological contribution. [P15](#p15), [P16](#p16), [P19](#p19), [P11](#p11)

### 5.2 Combinations that merit testing, without a “first” claim

**Occurrence-level provenance connected to branch-sensitive evaluation.** The reviewed sources offer structural context, explicit procedural topology, source-linked auditing and evidence extraction, but this search did not identify an inspected paper evaluating exactly the supplied combination of stable source occurrences, row/branch ownership, unspecified causes, and consolidated-edge evidence retention. That observation supports a focused research question, not a novelty conclusion. The strongest threats are [P01](#p01), [P04](#p04), [P05](#p05), [P13](#p13) and [P17](#p17), with [U01–U03](#u01) still requiring full inspection.

**Coverage-aware verification under a fixed resource budget.** The useful distinction is not whether a verifier exists, but whether structural recovery and selective semantic checks produce more *correctly grounded complete branches* for the same cost, rather than merely fewer accepted errors. The proposed experiment can connect the graph-correction and consistency literature to this maintenance-specific objective. [P06](#p06), [P15](#p15), [P19](#p19)

**Source-grouped human questions evaluated at matched final quality.** Relevant studies variously measure annotation time, agreement, interface completion time or modeled annotation expenditure. None of those measures is interchangeable with a controlled reduction in actual maintenance-KG review effort. A study of grouping and prioritization is therefore worthwhile, provided quality and retained information are controlled. [P10](#p10), [P11](#p11), [P12](#p12), [P20](#p20); unresolved comparison: [U06](#u06).

### 5.3 Safe positioning language for a draft

> We investigate a modular pipeline for constructing maintenance knowledge graphs from industrial manuals, combining document-structure-aware extraction, source-occurrence tracking, selective verification and source-grouped review. Building on prior work in procedural extraction, richly formatted knowledge construction and graph verification, we evaluate whether these design choices improve diagnostic-branch fidelity and reduce human review effort at comparable graph quality and coverage.

This is proposed framing, not a report of completed experiments. Replace “we evaluate” with the actual scope of the finished study. Do not replace it with “the first,” “hallucination-free,” “causally correct,” “ontology-independent,” or “reduces downtime” without separate supporting evidence.

## 6. Candidate novelty hypotheses and their strongest challenges

### H1. Branch-preserving extraction with explicit source-occurrence semantics

**Hypothesis:** Representing each diagnostic branch and its admissible source segments explicitly reduces cross-row/cross-branch associations while preserving recall.

**Closest challenges:** [P01](#p01) already exposes procedure mixing; [P13](#p13) supplies rich document context; [P05](#p05) extracts procedural topology; [P04](#p04) retains source information. The full text of [U01](#u01) could materially change the novelty assessment.

**Needed implementation/evidence:** Specify branch ownership, allowed context inheritance and the distinction between evidence and neighboring context. Add an evaluable mapping from source entries to expected fact sets. Test merged headers, continuation pages, multiple causes/remedies in one cell, exceptions and numbered alternatives. Show lower branch contamination at comparable branch recall, not just higher precision after discarding difficult rows.

**Contribution class:** Methodological only if the representation/algorithm is substantively distinct and tested against these alternatives; otherwise systems integration plus an empirical contribution.

### H2. Coverage-triggered recovery plus calibrated selective verification

**Hypothesis:** Structural signals and two extraction passes allocate additional extraction/verification more effectively than indiscriminate repeated prompting.

**Closest challenges:** [P15](#p15) for iterative graph correction; [P19](#p19) for sample consistency; [P06](#p06) for industrial repeatability/error analysis.

**Needed implementation/evidence:** Define the exact acceptance/tiering rule, recovery trigger and verifier input. Calibrate on held-out validation documents. Compare one longer call, two calls without verification, random additional calls, and targeted recovery at matched token/time budgets. Estimate the frequency of *shared wrong relations* when calls agree. Independent random seeds do not establish independent errors.

**Contribution class:** Most plausibly empirical or systems integration. A methodological claim requires a new decision/allocation mechanism, not just the combination of known checks.

### H3. Context- and provenance-preserving entity consolidation

**Hypothesis:** Consolidation that preserves occurrence identity and branch context prevents false diagnostic paths more effectively than lexical or semantic deduplication alone.

**Closest challenges:** [P03](#p03) for maintenance fusion, [P16](#p16) for semantic/schema canonicalization, and [P04](#p04)/[P13](#p13) for source information.

**Needed implementation/evidence:** Define entity identity separately from surface similarity. Make “cause unspecified in this branch” a scoped unknown or explicit absence state, not one global failure entity. Preserve evidence tuples, conditions, aliases and reviewer decisions through merges. Demonstrate fewer harmful overmerges without excessive fragmentation. Measure downstream spurious paths as well as ordinary clustering scores.

**Contribution class:** Systems integration unless a new context-aware matching method or enforceable representation invariant is introduced; empirical if the contribution is a rigorous characterization of the trade-off.

### H4. Budgeted, source-grouped human review

**Hypothesis:** Reviewing related source-based questions reduces actual human time compared with edge-by-edge review, without reducing final accuracy, branch completeness or source support.

**Closest challenges:** [P11](#p11) for document-centered semantic annotation; [P12](#p12) for prioritized human tagging; [P20](#p20) for uncertainty-based human/LLM allocation. [U06](#u06) is an unresolved, particularly important challenge.

**Needed implementation/evidence:** A reproducible grouping/ranking policy; separate human, agent and scripted reviewers in the logs; a controlled comparison of equivalent case sets; measured reading, checking, correcting and missing-fact recovery time. Demonstrate benefit across a budget curve and audit unreviewed accepted/excluded relations.

**Contribution class:** Human-centered systems and empirical contribution. Methodological only if grouping/allocation adds a defensible new mechanism beyond interface packaging.

### H5. A transferable, auditable maintenance-extraction benchmark and system

**Hypothesis:** A transparent evaluation package exposes failure modes hidden by conventional triple-only scores and allows reproducible comparisons across manuals/manufacturers.

**Closest challenges:** [P09](#p09)/[P10](#p10) for maintenance/repair benchmarks, [P05](#p05) for procedural reconstruction, and [P17](#p17)/[P18](#p18) for separate evidence evaluation.

**Needed implementation/evidence:** Release legally shareable manuals or a redistributable diagnostic subset, source-region annotations, branch/condition labels, occurrence-to-entity mappings, document-grouped splits, baseline adapters and evaluation code. Publish difficult and excluded cases, not just successful pages. A second manufacturer is a transfer test; a second ontology requires a separately specified schema-transfer experiment.

**Contribution class:** Empirical/resource contribution, accompanied by systems integration. It can remain valuable even when no individual pipeline component is novel.

## 7. Practical experimental design

Everything in this section is a **proposed study design**, not an assertion that the implementation already supports or has achieved it. Paper IDs identify the literature motivating each design choice.

### 7.1 Define the task and the gold standard before running models

Use three explicitly separated outputs:

**Source occurrences:** each extracted statement tied to its document version, page, segment and branch. An occurrence includes its qualifiers, action type and evidence context. A normalized triple alone is insufficient for judging whether its specific occurrence was extracted correctly.

**Consolidated graph:** entity clusters, aliases, normalized relations and the complete set of underlying source occurrences. A correct canonical edge can have one correct citation and another incorrect citation; score both levels.

**Review outcome:** accepted, uncertain, excluded and corrected assertions, including facts added by a reviewer because extraction missed them. Keep the pre-review graph so improvement and effort can be attributed.

Create gold annotations from the **whole selected diagnostic region**, not from model outputs. Two annotators should identify entities, relations, branch membership, conditions, source support and unspecified causes independently, followed by adjudication. Record disagreement rather than removing every disputed case from the evaluation. Separate genuinely ambiguous source content from model mistakes. P10’s filtering and P12’s agreement results make this distinction consequential. [P10](#p10), [P12](#p12)

For each statement, distinguish **explicitly supported**, **supported using specified inherited context**, **requires external domain inference**, **ambiguous**, and **not recoverable from the available document**. Decide which categories are in scope before evaluation. “The manual says X” and “X is physically/causally correct” require different gold standards. A source-grounded KG experiment alone cannot establish operational safety or causal validity.

### 7.2 Corpus and splits

An initial annotation pilot could use approximately **10–15 manuals** to refine the taxonomy and estimate annotation time; this is a planning suggestion, not a claimed statistically sufficient sample. For the confirmatory study, choose document and reviewer counts using pilot variance and the smallest practically relevant improvement. More pages from one manual do not substitute for independent manuals.

Include multiple manufacturers where access permits, with separate strata for prose, troubleshooting tables, numbered procedures, merged cells, page continuations and scanned/OCR text. Include negative/non-diagnostic pages when evaluating the page selector. Record manual age/version, language, document length, scan quality, domain and licensing. A corpus entirely composed of clean digital troubleshooting tables cannot substantiate OCR robustness.

Split at **document/product-family level**, grouping near-duplicate manuals, reused steps and manufacturer templates. Keep demonstrations, extraction rules, prompts, merge thresholds and verifier calibration out of test material. This is especially important when evaluating copied repair steps or repeated work-order patterns. [P09](#p09), [P10](#p10)

Report three progressively stronger settings only when actually run: held-out documents within known manufacturers; a held-out manufacturer; a held-out equipment domain. An English-only study does not demonstrate multilingual transfer, even though some reviewed papers use other languages. Reusing an extraction schema across documents does not prove ontology independence.

### 7.3 Baselines that isolate meaningful alternatives

**B0 — Deterministic structure/rules.** For clearly organized troubleshooting tables, map explicit symptom/cause/action columns and preserve row identity without an LLM. Add a modest domain lexicon or supervised tagger where justified. This is an adaptation inspired by P02, not a claim to reproduce its Korean pipeline unchanged. It tests whether clean-table performance requires generative extraction. [P02](#p02)

**B1 — Single-pass schema-guided LLM.** Same model, supplied ontology and document selection as the proposed system, but ordinary text chunks and one extraction call. Add a second version using the structured reading units but no repeated extraction or verifier. These are transparent internal baselines, not mislabeled published implementations. Use P08’s ontology-plus-demonstration strategy as an additional published-method adaptation where labeled examples are available. [P08](#p08)

**B2 — Supervised extraction.** Train a reproducible entity/relation model on the same available training annotations, following a MaintIE-style SpERT or REBEL recipe. Report annotation and training costs separately. A strong supervised baseline needs a learning curve; comparing a trained model with two labels against an LLM using many demonstrations is not informative. [P03](#p03), [P10](#p10)

**B3 — Procedural extraction.** On prose/list procedure subsets, adapt P01’s incremental ontology-based extraction. Evaluate the output with the study’s semantic/branch metrics rather than relying on ROUGE over Turtle. On flowchart subsets only, use FlowExtract where feasible; do not penalize a prose-only system for an unimplemented visual task without labeling the task mismatch. [P01](#p01), [P05](#p05)

**B4 — Verification and consolidation baselines.** Compare a PiVe-style trained verifier when suitable seed data exist, and a separately labeled prompt-only verifier when they do not. These are not equivalent reproductions. Compare no merging, lexical merging and a semantic canonicalization adaptation; separate relation-schema alignment from entity-identity resolution. [P15](#p15), [P16](#p16)

**B5 — Industrial general-purpose graph extraction.** Use a documented LangChain graph-transformer or GraphRAG extraction configuration, motivated by P06. Map its outputs into the target schema using a fixed, disclosed adapter. Report unmappable or missing statements rather than silently dropping them from evaluation. GraphRAG answer quality alone is not evidence of graph construction quality. [P06](#p06)

All model-based comparisons should use the same source inventory, permitted context and test split. Report both a **quality-oriented comparison** and a **budget-matched comparison**. A baseline that receives fewer relevant pages or a materially smaller token budget is not an adequate test of the pipeline design.

### 7.4 Required ablations

**Document structure.** Remove one feature family at a time: table headers/merged-cell inheritance, continuation reconstruction, step hierarchy, and reading-unit ownership with separately marked neighboring context. Also test fully flattened text. Report changes by source stratum, particularly wrong-row and wrong-branch relations. If the proposed ownership rule loses cross-page facts, that is an important negative result. [P13](#p13), [P14](#p14)

**Second extraction.** Compare one call, two-call union, two-call agreement-only acceptance, and the implemented tiering policy. Include a budget-matched longer single call. Estimate recall lost by agreement filtering and the proportion of agreed statements that remain wrong. Vary prompts or models only in a separately controlled experiment. [P06](#p06), [P19](#p19)

**Targeted recovery.** Compare no recovery, the unused-row trigger, and random/equal-budget additional extraction. Count genuinely newly recovered supported facts, duplicates and newly invented relations. A row being “used” is not proof all of its diagnostic facts were captured. [P15](#p15)

**Semantic verification.** Compare none, schema/lexical checks, agreement signals alone, and source-conditioned semantic verification. Evaluate the verifier itself on correct, unsupported, contradicted and partially supported relations, including wrong thresholds and omitted exceptions. Use a reviewer or independent gold annotation, not the same model’s agreement, as the assessment reference. [P17](#p17), [P18](#p18)

**Entity merging.** Compare no merge, string normalization, semantic matching and semantic matching plus context/provenance safeguards. Use a fixed candidate pool where possible to distinguish candidate-retrieval errors from matching errors. Include aliases, similarly named components in different assemblies, conflicting revisions and branch-scoped unspecified causes. [P03](#p03), [P16](#p16)

**Grouped review.** Compare edge-by-edge questions against source-grouped questions using equivalent content and acceptance rules. Add random versus uncertainty/coverage-based prioritization as a separate factor. Otherwise an apparent grouping benefit could actually be a ranking benefit. [P11](#p11), [P12](#p12), [P20](#p20)

**Budgets and operational recovery.** Sweep question/time budgets and acceptance thresholds; retain separate uncertain/excluded outputs. Record the effect of malformed/truncated-response recovery and failed calls. These mechanisms should improve completion without inventing missing text. Audit processing failures rather than removing them from the denominator.

A full factorial study may be impractical. Pre-register a primary comparison, use targeted one-factor ablations, and test interactions most likely to matter: structure×recovery, agreement×verification, and merging×branch preservation.

### 7.5 Metrics: relation, branch, evidence and consolidation

**Relation accuracy.** Report micro and document-macro precision, recall and F1 using a predeclared strict match over typed subject–relation–object. Add separately reported relaxed matching with fixed alias rules; do not let an LLM judge freely redefine equivalence. Break down results by relation type, input structure, manufacturer and difficulty. Report counts as well as percentages. Missing gold facts remain false negatives after filtering, abstention or exclusion.

**Diagnostic-branch correctness.** Define a branch as the source-supported combination of symptom/code, cause or explicit unspecified status, required tests/actions, affected component and applicable qualifiers. Measure exact branch accuracy/recall, branch-level precision, and cross-branch contamination. Compute a complete-chain metric only for chains the source actually specifies. Do not assume every symptom–cause and cause–action pair forms a valid Cartesian combination. Report “no complete branch recovered” even when many individual triples are correct. This complements P05’s node/edge distinction and P01’s procedural error examples. [P01](#p01), [P05](#p05)

**Conditions and order.** Evaluate condition coverage, negation, comparison operator, value/unit, exception scope, action type and explicit precedence edges separately. Textual similarity between condition strings is not enough when `above` becomes `below` or an exception moves to another action. If the system lacks executable semantics, label this **condition/precedence preservation**, not diagnostic execution correctness.

**Source grounding.** Distinguish (a) valid segment IDs, (b) correct excerpt reconstruction, (c) the cited text actually supporting the relation, and (d) support for all qualifiers and branch context. Define **joint grounded-relation precision** as the fraction of accepted relations that are both semantically correct and adequately supported by their cited evidence. Also report grounded-relation recall against the full eligible gold set. An edge may require several fragments, such as a row plus inherited header; evidence gold should allow explicit alternative adequate evidence sets. [P17](#p17), [P18](#p18)

**Occurrence versus consolidated coverage.** Score extraction over source occurrences before deduplication and over canonical facts after deduplication. This prevents repeated correct facts from inflating graph coverage and prevents merging from hiding lost citations. Measure the fraction of source occurrences whose provenance survives consolidation exactly.

**Merge quality.** Use pairwise and/or B-cubed cluster precision/recall alongside rates of harmful overmerges, undermerges and lost aliases. Add a maintenance-specific count of spurious diagnostic paths introduced by merging. Distinguish merging two genuine occurrences of one fault from merging two unrelated “unspecified cause” placeholders. Ordinary clustering F1 can obscure the latter error’s practical effect.

**Risk and abstention.** Report accepted-set error rate against acceptance fraction, but also plot accepted *gold-fact recall* and complete-branch recall. The fraction of predictions retained is not the fraction of source knowledge recovered. Include a separately adjudicated audit sample of high-confidence accepted items, uncertain items and excluded items. Sampling weights must be used when estimating corpus-wide rates from unequal audit strata.

### 7.6 Actual human effort: prevent apparent savings from suppressed work

Use a randomized, counterbalanced study with maintenance-domain reviewers where possible. Compare equivalent but nonidentical source blocks across conditions to limit memory effects. Record reviewer expertise and train participants on the interface and ontology before the timed portion. A within-person crossover design can reduce reviewer-speed variation, but still requires document/case balancing.

Measure **active human minutes**, source-reading time, navigation/context switches, decisions, edits, additional missing facts recovered and elapsed session time separately. Distinguish initial ontology/prompt setup, annotation used to train a verifier, graph-review work and final audit. Do not count agent/scripted review as human work or claim savings by replacing a human with an unmeasured automated decision.

The primary efficiency endpoint should be **time to reach comparable final quality and coverage**, or, under a fixed time budget, final grounded-relation and complete-branch performance. Predefine practically acceptable quality margins before seeing the results; they should be justified by the application, not copied from unrelated benchmarks.

A lower question count can mean fewer context switches, but it can also mean that hard questions were never asked. To distinguish these explanations, keep the same gold inventory across conditions, inspect residual omissions after the timed task, and conduct a blinded final audit of accepted and excluded content. Report the time required to recover missed information. A system that asks half as many questions while missing twice as many facts has not demonstrated equivalent-work efficiency.

Log correct acceptances, false acceptances, unnecessary rejections, corrected errors and unresolved cases. Report the quality of human corrections themselves; human review is not infallible. Group-level approval also deserves scrutiny because one correct item may encourage acceptance of several incorrect neighbors. The different evidence types in P10–P12 and P20 motivate measuring these quantities directly rather than treating all “human effort” claims as comparable. [P10](#p10), [P11](#p11), [P12](#p12), [P20](#p20)

### 7.7 Costs, uncertainty and optional downstream evaluation

Record preprocessing/OCR time, every extraction/verification/recovery call, input/output tokens, retries, truncated outputs, model versions, context limits, hardware and parallelism. Separate one-time training/setup costs from per-manual inference and human review. Use the actual price schedule on the experiment date; historical paper costs are not current prices. Report cost per manual, per 100 eligible gold facts and per correctly grounded accepted fact, not only cost per generated triple. [P15](#p15)

Repeat stochastic extraction runs with a predeclared seed/prompt policy. Use paired, document-clustered confidence intervals or hierarchical analyses; relations within one manual are not independent observations. For reviewer studies, account for both reviewer and document effects. Identify a small number of primary endpoints and treat the remaining analyses as secondary. Report negative and null ablations.

A downstream extension can compare **text RAG**, **generated-KG-assisted retrieval**, and an **oracle/gold-KG-assisted condition** on the same maintenance questions. Separate answer correctness, adequate source citation, diagnostic-path correctness and abstention. The oracle condition helps distinguish graph construction failures from retrieval/answer-generation failures. None of these offline results establishes reduced equipment downtime, avoided service visits or safety benefits without a separate operational study. [P04](#p04), [P06](#p06), [P07](#p07)

## 8. Highly relevant published works without successfully inspected full text

**These eight entries are not included in the 20-paper technical comparison or its numerical synthesis.** Their publication records were identified, but a legal full-text copy could not be successfully retrieved and inspected during this search. “Not retrieved” does not mean “not open access”: some publisher pages label the paper open access, yet the available reading routes failed. Publisher abstracts are sufficient to flag relevance, not to establish detailed methods, results or limitations.

| ID | Published paper and authors | Verified publication record / official landing | Access outcome and why it remains important |
| --- | --- | --- | --- |
| <a id="u01"></a>**U01** | **A task-centric knowledge graph construction method based on multi-modal representation learning for industrial maintenance automation**. Zengkun Liu; Yuqian Lu. | *Engineering Reports* 6(12), e12952 (2024); first online 7 July 2024. [DOI / publisher](https://onlinelibrary.wiley.com/doi/10.1002/eng2.12952). | Wiley full/epdf/pdf routes did not yield inspectable full text. Very close task-centric, multimodal maintenance construction; obtain before claiming a new layout-aware maintenance method. No full-text results adopted here. |
| <a id="u02"></a>**U02** | **Generating Troubleshooting Trees for Industrial Equipment using Large Language Models (LLM)**. Lasitha Vidyaratne; Xian Yeow Lee; Aman Kumar; Tsubasa Watanabe; Ahmed Farahat; Chetan Gupta. | IEEE ICPHM 2024, pp. 116–125. DOI **10.1109/ICPHM61352.2024.10626823**. [IEEE record](https://ieeexplore.ieee.org/document/10626823). | Published full conference paper identified; no inspectable legal full-text copy retrieved. Direct challenge to diagnostic-structure extraction. Abstract-only findings not imported into the main set. |
| <a id="u03"></a>**U03** | **Generating Troubleshooting Trees With FMEA Using Large Language Models (LLM)**. Lasitha Vidyaratne; Huijuan Shao; Tsubasa Watanabe; Ahmed Farahat; Chetan Gupta. | IEEE ICPHM 2025, pp. 1–10. DOI **10.1109/ICPHM65385.2025.11062049**. [IEEE record](https://ieeexplore.ieee.org/document/11062049). | No inspectable full text retrieved. FMEA/troubleshooting-tree focus is highly relevant. Distinct title/publication from U02; the substantive extent of extension could not be established without the paper. |
| <a id="u04"></a>**U04** | **MWO2KG and Echidna: Constructing and exploring knowledge graphs from maintenance data**. Michael Stewart; Melinda Hodkiewicz; Wei Liu; Tim French. | *Proceedings of the Institution of Mechanical Engineers, Part O: Journal of Risk and Reliability* 238(5), 920–932 (2024); first online 5 November 2022. [Publisher / DOI 10.1177/1748006X221131128](https://journals.sagepub.com/doi/10.1177/1748006X221131128); [UWA publication record](https://research-repository.uwa.edu.au/en/publications/mwo2kg-and-echidna-constructing-and-exploring-knowledge-graphs-fr/). | Publisher full text was not retrieved; the inspected institutional record did not provide an accessible manuscript. Maintenance work orders, not manuals. Relevant extraction/fusion and exploration comparator. |
| <a id="u05"></a>**U05** | **Text2KGBench: A Benchmark for Ontology-Driven Knowledge Graph Generation from Text**. Nandana Mihindukulasooriya; Sanju Tiwari; Carlos F. Enguix; Kusum Lata. | ISWC 2023, LNCS 14266, pp. 247–265. [Publisher / DOI 10.1007/978-3-031-47243-5_14](https://link.springer.com/chapter/10.1007/978-3-031-47243-5_14). | Landing page/abstract accessible; full chapter not retrieved. No legal non-arXiv manuscript successfully located. Relevant ontology-conformance benchmark; do not infer semantic grounding from its title. |
| <a id="u06"></a>**U06** | **Human Evaluation of Procedural Knowledge Graph Extraction from Text with Large Language Models**. Valentina Anita Carriero; Antonia Azzini; Ilaria Baroni; Mario Scrocca; Irene Celino. | EKAW 2024, LNCS 15370, pp. 434–452; publisher citation year 2025; first online 20 November 2024. [Publisher / DOI 10.1007/978-3-031-77792-9_26](https://link.springer.com/chapter/10.1007/978-3-031-77792-9_26). | Full chapter not retrieved. Crucial unresolved procedural/human-evaluation comparison. A software repository is not a substitute for inspecting its experimental protocol; no review-time claim is attributed here. |
| <a id="u07"></a>**U07** | **Automatic construction of asset knowledge graph with large language model**. Tomoaki Morioka; Toshiaki Kono; Takehisa Nishida. | *Procedia CIRP* 135, 762–767 (2025). DOI **10.1016/j.procir.2025.01.097**. [Official publication](https://www.sciencedirect.com/science/article/pii/S2212827125004469). | Publisher labels it open access, but only abstract/metadata were retrieved. FMEA-oriented asset knowledge plus expert refinement is highly relevant. Abstract precision/recall numbers are deliberately not treated as inspected results. |
| <a id="u08"></a>**U08** | **Trustworthy-by-Design Generative AI Assistants for Industrial Troubleshooting: A Knowledge Graph Grounded Architecture**. Rohan Jadhav; Emmanuel Papadakis; George Baryannis. | TRUST-AI 2026, CEUR Workshop Proceedings 4254, pp. 164–173. [Official volume](https://ceur-ws.org/Vol-4254/). | Volume records peer review: 38 submissions, 22 accepted; this is a ten-page research paper. Individual full-text retrieval not completed. Strong recent architecture-level relevance; no methods/results inferred from its title. |

The restricted main set should therefore **not** be described as an exhaustive review of the closest published industrial work. The access-limited set is a substantive limitation for novelty assessment, not a set of weak or irrelevant papers.

## 9. Compact search log and screening decisions

### 9.1 Search design and sources

This was a **critical, purposive literature search with citation chasing**, not a registered systematic review. Searches were run on **27 September 2026**, using the inclusive **2016-09-27 to 2026-09-27** publication interval. Older foundational citations encountered inside eligible papers were not automatically added. Later nominal publication years were checked against verified online-first dates.

Discovery combined web-indexed scholarly searches and Exa scholarly/web discovery. Verification and technical reading used official ACL Anthology, ACM, Springer, MDPI, CEUR, IEEE/CVF and PHM publication sources, plus NIST, PMC, Stanford, TIB, University of Brescia and University of Western Australia institutional records/copies where appropriate. Exa publication summaries, search snippets and secondary indexes were discovery aids only. No direct subscription search of Scopus or Web of Science was performed, and no completeness claim for those indexes is made.

The following table groups the executed complementary searches by purpose; query expressions summarize the query families rather than pretending all engines received identical Boolean syntax. Exact-title/DOI follow-up searches were used for candidate verification and legal full-text discovery.

| Search family | Query formulation used/adapted | Sources followed and screening purpose |
| --- | --- | --- |
| Manuals → knowledge | Maintenance/service/technical manuals or troubleshooting + knowledge graph construction / knowledge extraction / ontology population | Industrial papers, publisher records and institutional full texts; prioritize manuals over generic KG surveys. |
| Industrial NLP | Industrial/manufacturing/maintenance + information/relation extraction + documentation/reports/work orders; older rule-based and supervised work | MDPI, ACL, NIST/PHM, UWA and publisher records; retain pre-LLM alternatives and label input differences. |
| Diagnostic structures | Fault/troubleshooting knowledge + acquisition/graph + documents/manuals; exact troubleshooting-tree and FlowExtract titles | IEEE, Springer and CEUR; distinguish automatically extracted branches from hand-modeled diagnostic ontologies. |
| Grounding and verification | LLM KG construction + evidence/provenance/verification; PiVe, evidence-guided relation extraction and claim entailment | ACL and primary PDFs; distinguish selected evidence from entailed relations and sampling agreement from truth. |
| Layout and procedures | Technical documents + table/document structure/procedural extraction; Fonduer, PubTables, procedural K-CAP papers | ACM, CVF, Stanford and institutional archives; inspect structure and evaluation units. |
| Human work | KG/relation extraction + human-in-the-loop, annotation cost, selective review/uncertainty; Nestor agreement, ONTO-PAWLS, CoAnnotating | PHM/NIST, ACM and ACL; distinguish observed time, annotation count and modeled cost. |
| Consolidation | Industrial/maintenance KG + entity resolution, linking, canonicalization; exact EDC and equipment-fusion follow-ups | Publisher full text and ACL; distinguish entity merging from relation-schema canonicalization. |
| Equipment-specific | Injection molding/moulding, machinery, maintenance/troubleshooting + knowledge extraction/manuals | Broad discovery plus industrial citation chains. No inspected main-set paper specifically established the exact injection-moulding-manual pipeline; this is not evidence of novelty. |

**Backward citation checks:** the Bosch paper led back to task-centric maintenance construction; procedural work connected to repair/manual annotation; the maintenance short-text paper connected to MaintIE and Text2KGBench; Nestor agreement connected to earlier maintenance-tagging work; general graph verification/canonicalization papers connected to their published baselines. **Forward/citing-work checks:** searches around MaintIE, task-centric industrial construction and procedural extraction surfaced later maintenance LLM systems and the human-evaluation chapter. These checks were targeted, not an exhaustive enumeration of every citing paper.

### 9.2 Deduplication and limits

Preprint and published versions were consolidated under the published record. No arXiv URL is offered as a main reading link. P01/P11 are separate K-CAP papers with different methods/studies, not duplicates; P08/P10 respectively evaluate a method and introduce its underlying maintenance benchmark. U02/U03 are separate publications, but their extension relationship remains technically unverified. A review article encountered during discovery was not used to replace direct inspection of an original method.

**Final report accounting:** 20 included full-text-inspected papers; eight relevant publication-verified, full-text-uninspected papers; additional rejected or unresolved candidates. Global retrieval and screening totals were not captured reproducibly, so no invented PRISMA-style count is supplied. Main-set publication dates start in 2018, although searches covered the full ten-year interval and explicitly included older non-LLM approaches. The recent end of the interval is represented, but the search cannot guarantee discovery of every newly indexed September 2026 paper.

### 9.3 Representative exclusions and unresolved candidates

Sensor-only prediction, vibration diagnosis, remaining-useful-life studies and manually authored maintenance ontologies without document-extraction or review methods were excluded on scope. Commercial GraphRAG documentation can describe a baseline implementation, but is not counted as a peer-reviewed paper. Preprint-only procedural/flowchart work and unverified later versions of table datasets were excluded from the confirmed set.

The discovered **“Generation of Semantic Knowledge Graphs from Maintenance Work Order Data”** appeared through an open-review/submission route; a completed peer-reviewed publication was not independently established in this search. **“Extracting Semantics from Maintenance Records”** was also not admitted without sufficient publication/review verification. **“Nestor: A Tool for Natural Language Annotation of Short Texts”** was not counted merely to enlarge the set; the full empirical agreement study P12 provides the more relevant research evidence here.

**“CoMA-IKG: LLM-Driven Multiagent Framework for Automated Construction of Industrial Knowledge Graph”** was discovered as a potentially important 2026 candidate, but publisher/full-text verification was not completed sufficiently for the confirmed main set. It should not be cited here as established evidence for a detailed multiagent extraction method. Likewise, a preprint's existence or a DOI-shaped string was never used alone to infer peer review.

Access failures included publisher restrictions, crawler failures and PDF-rendering failures. These were treated separately: a paper could enter the main set when its complete legal HTML/PDF text was inspectable despite a screenshot failure; it stayed outside when only an abstract or metadata could be read. No unlicensed mirror was used to bypass an inaccessible paper.

## 10. Verified BibTeX for the 20 included papers

Entries below use the publication record, not a preprint citation. Optional fields that were not verified are omitted. Stable proceedings identifiers are retained where no DOI is asserted. P05 deliberately uses Springer's citation year **2027**, with its eligible online publication date recorded in the note. P04 retains the publisher's **2024** issue citation. Reading-copy versions are described in Table 1 rather than silently treating every institutional PDF as the publisher's version of record.

```bibtex
@inproceedings{P01,
  title = {Procedural Text Mining with Large Language Models},
  author = {Rula, Anisa and D'Souza, Jennifer},
  year = {2023},
  booktitle = {Proceedings of the 12th Knowledge Capture Conference 2023},
  pages = {9--16},
  publisher = {Association for Computing Machinery},
  doi = {10.1145/3587259.3627572},
  url = {https://dl.acm.org/doi/10.1145/3587259.3627572}
}

@article{P02,
  title = {A Named Entity and Relationship Extraction Method from Trouble-Shooting Documents in Korean},
  author = {Jeong, Minkyu and Suh, Hyowon and Lee, Heejung and Lee, Jae Hyun},
  year = {2022},
  journal = {Applied Sciences},
  volume = {12},
  number = {23},
  pages = {11971},
  doi = {10.3390/app122311971},
  url = {https://www.mdpi.com/2076-3417/12/23/11971}
}

@article{P03,
  title = {Knowledge Graph Construction Based on a Joint Model for Equipment Maintenance},
  author = {Lou, Ping and Yu, Dan and Jiang, Xuemei and Hu, Jiwei and Zeng, Yuhang and Fan, Chuannian},
  year = {2023},
  journal = {Mathematics},
  volume = {11},
  number = {17},
  pages = {3748},
  doi = {10.3390/math11173748},
  url = {https://www.mdpi.com/2227-7390/11/17/3748}
}

@article{P04,
  title = {Fault Knowledge Graph Construction and Platform Development for Aircraft PHM},
  author = {Meng, Xiangzhen and Jing, Bo and Wang, Shenglong and Pan, Jinxin and Huang, Yifeng and Jiao, Xiaoxuan},
  year = {2024},
  journal = {Sensors},
  volume = {24},
  number = {1},
  pages = {231},
  doi = {10.3390/s24010231},
  url = {https://www.mdpi.com/1424-8220/24/1/231},
  note = {Issue citation year 2024; first published online 2023-12-30}
}

@inproceedings{P05,
  title = {FlowExtract: Procedural Knowledge Extraction from Maintenance Flowcharts},
  author = {Gil de Avalle, Guillermo and Maruster, Laura and Sloot, Eric and Emmanouilidis, Christos},
  year = {2027},
  booktitle = {Advances in Production Management Systems: Shaping the Future of Industry Through Sustainable, Data-Driven, and Human-Centric Production Systems},
  series = {IFIP Advances in Information and Communication Technology},
  volume = {808},
  pages = {354--369},
  publisher = {Springer},
  doi = {10.1007/978-3-032-38594-9_24},
  url = {https://link.springer.com/chapter/10.1007/978-3-032-38594-9_24},
  note = {APMS 2026; first published online 2026-09-21, within the search interval; publisher citation year 2027}
}

@inproceedings{P06,
  title = {Towards Efficient Field Service Engineering for Powertrains via LLM-generated Knowledge Graphs},
  author = {Juhlin, Prerna and Hussein, Rana and Schoch, Nicolai},
  year = {2025},
  booktitle = {Proceedings of the Second International Workshop on Scaling Knowledge Graphs for Industry (SKGi 2025)},
  series = {CEUR Workshop Proceedings},
  volume = {4064},
  publisher = {CEUR-WS.org},
  url = {https://ceur-ws.org/Vol-4064/SKGi-paper2.pdf},
  note = {Stable proceedings identifier: Vol-4064/SKGi-paper2; eight-page research paper}
}

@inproceedings{P07,
  title = {Knowledge Graph Construction towards a Graph RAG-Enhanced Intelligent Maintenance Chatbot},
  author = {Zhang, Hansi and Schmidt, Wilma Johanna and Shen, Xiaozhi and Cao, Qiushi and Monka, Sebastian and Paschke, Adrian},
  year = {2025},
  booktitle = {Proceedings of the Second International Workshop on Scaling Knowledge Graphs for Industry (SKGi 2025)},
  series = {CEUR Workshop Proceedings},
  volume = {4064},
  publisher = {CEUR-WS.org},
  url = {https://ceur-ws.org/Vol-4064/SKGi-paper3.pdf},
  note = {Stable proceedings identifier: Vol-4064/SKGi-paper3; seven-page research paper}
}

@inproceedings{P08,
  title = {Ontology-guided Knowledge Graph Construction from Maintenance Short Texts},
  author = {van Cauter, Zeno and Yakovets, Nikolay},
  year = {2024},
  booktitle = {Proceedings of the 1st Workshop on Knowledge Graphs and Large Language Models (KaLLM 2024)},
  pages = {75--84},
  publisher = {Association for Computational Linguistics},
  doi = {10.18653/v1/2024.kallm-1.8},
  url = {https://aclanthology.org/2024.kallm-1.8/}
}

@inproceedings{P09,
  title = {MyFixit: An Annotated Dataset, Annotation Tool, and Baseline Methods for Information Extraction from Repair Manuals},
  author = {Nabizadeh, Nima and Kolossa, Dorothea and Heckmann, Martin},
  year = {2020},
  booktitle = {Proceedings of the Twelfth Language Resources and Evaluation Conference},
  pages = {2120--2128},
  publisher = {European Language Resources Association},
  url = {https://aclanthology.org/2020.lrec-1.260/},
  note = {ACL Anthology stable identifier: 2020.lrec-1.260}
}

@inproceedings{P10,
  title = {MaintIE: A Fine-Grained Annotation Schema and Benchmark for Information Extraction from Maintenance Short Texts},
  author = {Bikaun, Tyler K. and French, Tim and Stewart, Michael and Liu, Wei and Hodkiewicz, Melinda},
  year = {2024},
  booktitle = {Proceedings of the 2024 Joint International Conference on Computational Linguistics, Language Resources and Evaluation (LREC-COLING 2024)},
  pages = {10939--10951},
  publisher = {ELRA and ICCL},
  url = {https://aclanthology.org/2024.lrec-main.954/},
  note = {ACL Anthology stable identifier: 2024.lrec-main.954}
}

@inproceedings{P11,
  title = {Annotation and Extraction of Industrial Procedural Knowledge from Textual Documents},
  author = {Rula, Anisa and Re Calegari, Gloria and Azzini, Antonia and Baroni, Ilaria and Celino, Irene},
  year = {2023},
  booktitle = {Proceedings of the 12th Knowledge Capture Conference 2023},
  publisher = {Association for Computing Machinery},
  doi = {10.1145/3587259.3627570},
  url = {https://dl.acm.org/doi/10.1145/3587259.3627570}
}

@inproceedings{P12,
  title = {Agreement Behavior of Isolated Annotators for Maintenance Work-Order Data Mining},
  author = {Hastings, Emily M. and Sexton, Thurston and Brundage, Michael P. and Hodkiewicz, Melinda},
  year = {2019},
  booktitle = {Proceedings of the Annual Conference of the PHM Society},
  volume = {11},
  number = {1},
  publisher = {PHM Society},
  doi = {10.36001/phmconf.2019.v11i1.791},
  url = {https://papers.phmsociety.org/index.php/phmconf/article/view/791}
}

@inproceedings{P13,
  title = {Fonduer: Knowledge Base Construction from Richly Formatted Data},
  author = {Wu, Sen and Hsiao, Luke and Cheng, Xiao and Hancock, Braden and Rekatsinas, Theodoros and Levis, Philip and Ré, Christopher},
  year = {2018},
  booktitle = {Proceedings of the 2018 International Conference on Management of Data},
  publisher = {Association for Computing Machinery},
  doi = {10.1145/3183713.3183729},
  url = {https://dl.acm.org/doi/10.1145/3183713.3183729},
  note = {SIGMOD 2018; institutional accepted manuscript inspected}
}

@inproceedings{P14,
  title = {PubTables-1M: Towards Comprehensive Table Extraction From Unstructured Documents},
  author = {Smock, Brandon and Pesala, Rohith and Abraham, Robin},
  year = {2022},
  booktitle = {Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition},
  pages = {4634--4642},
  publisher = {IEEE},
  doi = {10.1109/CVPR52688.2022.00459},
  url = {https://openaccess.thecvf.com/content/CVPR2022/html/Smock_PubTables-1M_Towards_Comprehensive_Table_Extraction_From_Unstructured_Documents_CVPR_2022_paper.html}
}

@inproceedings{P15,
  title = {PiVe: Prompting with Iterative Verification Improving Graph-based Generative Capability of LLMs},
  author = {Han, Jiuzhou and Collier, Nigel and Buntine, Wray and Shareghi, Ehsan},
  year = {2024},
  booktitle = {Findings of the Association for Computational Linguistics: ACL 2024},
  pages = {6702--6718},
  publisher = {Association for Computational Linguistics},
  doi = {10.18653/v1/2024.findings-acl.400},
  url = {https://aclanthology.org/2024.findings-acl.400/}
}

@inproceedings{P16,
  title = {Extract, Define, Canonicalize: An LLM-based Framework for Knowledge Graph Construction},
  author = {Zhang, Bowen and Soh, Harold},
  year = {2024},
  booktitle = {Proceedings of the 2024 Conference on Empirical Methods in Natural Language Processing},
  pages = {9820--9836},
  publisher = {Association for Computational Linguistics},
  doi = {10.18653/v1/2024.emnlp-main.548},
  url = {https://aclanthology.org/2024.emnlp-main.548/}
}

@inproceedings{P17,
  title = {DREEAM: Guiding Attention with Evidence for Improving Document-Level Relation Extraction},
  author = {Ma, Youmi and Wang, An and Okazaki, Naoaki},
  year = {2023},
  booktitle = {Proceedings of the 17th Conference of the European Chapter of the Association for Computational Linguistics},
  pages = {1971--1983},
  publisher = {Association for Computational Linguistics},
  doi = {10.18653/v1/2023.eacl-main.145},
  url = {https://aclanthology.org/2023.eacl-main.145/}
}

@inproceedings{P18,
  title = {WiCE: Real-World Entailment for Claims in Wikipedia},
  author = {Kamoi, Ryo and Goyal, Tanya and Rodriguez, Juan Diego and Durrett, Greg},
  year = {2023},
  booktitle = {Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing},
  pages = {7561--7583},
  publisher = {Association for Computational Linguistics},
  doi = {10.18653/v1/2023.emnlp-main.470},
  url = {https://aclanthology.org/2023.emnlp-main.470/}
}

@inproceedings{P19,
  title = {SelfCheckGPT: Zero-Resource Black-Box Hallucination Detection for Generative Large Language Models},
  author = {Manakul, Potsawee and Liusie, Adian and Gales, Mark},
  year = {2023},
  booktitle = {Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing},
  pages = {9004--9017},
  publisher = {Association for Computational Linguistics},
  doi = {10.18653/v1/2023.emnlp-main.557},
  url = {https://aclanthology.org/2023.emnlp-main.557/}
}

@inproceedings{P20,
  title = {CoAnnotating: Uncertainty-Guided Work Allocation between Human and Large Language Models for Data Annotation},
  author = {Li, Minzhi and Shi, Taiwei and Ziems, Caleb and Kan, Min-Yen and Chen, Nancy and Liu, Zhengyuan and Yang, Diyi},
  year = {2023},
  booktitle = {Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing},
  pages = {1487--1505},
  publisher = {Association for Computational Linguistics},
  doi = {10.18653/v1/2023.emnlp-main.92},
  url = {https://aclanthology.org/2023.emnlp-main.92/}
}
```
