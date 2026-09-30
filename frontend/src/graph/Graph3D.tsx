import ForceGraph3D, { type ForceGraph3DInstance } from "3d-force-graph";
import { useEffect, useImperativeHandle, useRef, type Ref } from "react";
import * as THREE from "three";
import type { Tier } from "../api/types";
import { TYPE_LABEL } from "../text/it";
import { DIMMED, EDGE_STYLE, edgeLook, NODE_STYLE } from "./style";

export interface ViewNode {
  id: string;
  type: string;
  name: string;
}

export interface ViewLink {
  id: string;
  type: string;
  from: string;
  to: string;
  tier: Tier | null;
  derived?: boolean;
}

export interface GraphHandle {
  /** Let the layout move again after the person froze it by touching the scene. */
  relayout: () => void;
  fit: () => void;
}

interface SimNode extends ViewNode {
  x?: number;
  y?: number;
  z?: number;
  fx?: number;
  fy?: number;
  fz?: number;
  mesh?: THREE.Mesh;
  label?: THREE.Sprite;
  born?: number;
}

interface SimLink {
  id: string;
  source: string | SimNode;
  target: string | SimNode;
  view: ViewLink;
  line?: THREE.Line;
}

const SIZE = 1.6; // world units per radius step
const GROW_MS = 240;
const reducedMotion = () => window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;

function escapeHtml(text: string): string {
  return text.replace(/[&<>"']/g, (char) => `&#${char.charCodeAt(0)};`);
}

function makeMesh(node: SimNode): THREE.Mesh {
  const style = NODE_STYLE[node.type] ?? NODE_STYLE.Component;
  const mesh = new THREE.Mesh(
    new THREE.SphereGeometry(style.radius * SIZE, 20, 14),
    new THREE.MeshLambertMaterial({ color: style.color, transparent: true, opacity: 1 }),
  );
  return mesh;
}

const LABEL_CHARACTERS = 32;

/** The node's name as a flat sprite beside it, always turned to the camera. */
function makeLabel(node: SimNode): THREE.Sprite {
  const text = node.name.length > LABEL_CHARACTERS ? `${node.name.slice(0, LABEL_CHARACTERS - 1)}…` : node.name;
  const canvas = document.createElement("canvas");
  const context = canvas.getContext("2d")!;
  const font = "600 28px Onest, system-ui, sans-serif";
  context.font = font;
  canvas.width = Math.ceil(context.measureText(text).width) + 16;
  canvas.height = 40;
  context.font = font;
  context.fillStyle = "rgba(12, 10, 9, 0.72)";
  context.fillRect(0, 0, canvas.width, canvas.height);
  context.fillStyle = "#e7e5e4";
  context.textBaseline = "middle";
  context.fillText(text, 8, canvas.height / 2);
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: texture, transparent: true, depthWrite: false }));
  const height = 3.2;
  sprite.scale.set((height * canvas.width) / canvas.height, height, 1);
  const radius = (NODE_STYLE[node.type] ?? NODE_STYLE.Component).radius * SIZE;
  sprite.position.set(0, radius + height * 0.8, 0);
  return sprite;
}

function makeLine(link: SimLink): THREE.Line {
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.BufferAttribute(new Float32Array(6), 3));
  const line = new THREE.Line(geometry);
  styleLine(line, link.view, 1);
  return line;
}

function styleLine(line: THREE.Line, view: ViewLink, dim: number) {
  const look = edgeLook(view.tier, view.derived);
  const style = EDGE_STYLE[look ?? "proposed"];
  const opacity = look === null ? 0 : style.opacity * dim;
  const current = line.material as THREE.LineBasicMaterial;
  const wantDashed = style.dashed;
  if (!(current instanceof THREE.LineBasicMaterial) || (current instanceof THREE.LineDashedMaterial) !== wantDashed) {
    current?.dispose?.();
    line.material = wantDashed
      ? new THREE.LineDashedMaterial({ color: style.color, dashSize: 2, gapSize: 2, transparent: true, opacity })
      : new THREE.LineBasicMaterial({ color: style.color, transparent: true, opacity });
  } else {
    current.color.set(style.color);
    current.opacity = opacity;
  }
  line.visible = look !== null;
}

export function Graph3D({
  nodes,
  links,
  focus,
  onNodeClick,
  onLinkClick,
  onBackgroundClick,
  handle,
  labels = false,
}: {
  nodes: ViewNode[];
  links: ViewLink[];
  focus?: Set<string> | null;
  onNodeClick?: (id: string) => void;
  onLinkClick?: (id: string) => void;
  onBackgroundClick?: () => void;
  handle?: Ref<GraphHandle>;
  /** Names always shown beside the nodes, not only on hover. */
  labels?: boolean;
}) {
  const container = useRef<HTMLDivElement>(null);
  const graph = useRef<ForceGraph3DInstance | null>(null);
  const nodeMap = useRef(new Map<string, SimNode>());
  const linkMap = useRef(new Map<string, SimLink>());
  const callbacks = useRef({ onNodeClick, onLinkClick, onBackgroundClick });
  callbacks.current = { onNodeClick, onLinkClick, onBackgroundClick };
  const fitted = useRef(false);
  const touched = useRef(false);
  const frame = useRef(0);
  const withLabels = useRef(labels);
  withLabels.current = labels;

  // One accessor for the node objects: a sphere, and its name when the labels are on.
  const nodeObject = (node: object) => {
    const sim = node as SimNode;
    sim.mesh = makeMesh(sim);
    if (sim.born && !reducedMotion()) sim.mesh.scale.setScalar(0.001);
    if (!withLabels.current) {
      sim.label = undefined;
      return sim.mesh;
    }
    const group = new THREE.Group();
    sim.label = makeLabel(sim);
    group.add(sim.mesh, sim.label);
    return group;
  };

  // New nodes grow to their size; the loop runs only while some node is growing.
  const grow = () => {
    const now = performance.now();
    let growing = false;
    for (const node of nodeMap.current.values()) {
      if (!node.born) continue;
      if (!node.mesh) {
        growing = true;
        continue;
      }
      const share = Math.min(1, (now - node.born) / GROW_MS);
      node.mesh.scale.setScalar(Math.max(0.001, share));
      if (share >= 1) node.born = undefined;
      else growing = true;
    }
    frame.current = growing ? requestAnimationFrame(grow) : 0;
  };

  useImperativeHandle(handle, () => ({
    relayout: () => {
      for (const node of nodeMap.current.values()) {
        delete node.fx;
        delete node.fy;
        delete node.fz;
      }
      graph.current?.d3ReheatSimulation();
    },
    fit: () => graph.current?.zoomToFit(reducedMotion() ? 0 : 400, 48),
  }));

  // One scene for the life of the component.
  useEffect(() => {
    const element = container.current;
    if (!element) return;
    const instance = new ForceGraph3D(element, { controlType: "orbit" })
      .backgroundColor("#0c0a09")
      .showNavInfo(false)
      .nodeId("id")
      .nodeThreeObject(nodeObject)
      .nodeLabel((node: object) => {
        const sim = node as SimNode;
        return `${escapeHtml(sim.name)}<br>${escapeHtml(TYPE_LABEL[sim.type] ?? sim.type)}`;
      })
      .linkThreeObject((link: object) => {
        const sim = link as SimLink;
        sim.line = makeLine(sim);
        return sim.line;
      })
      .linkPositionUpdate((object: THREE.Object3D, { start, end }) => {
        const line = object as THREE.Line;
        const position = line.geometry.getAttribute("position") as THREE.BufferAttribute;
        position.setXYZ(0, start.x, start.y, start.z);
        position.setXYZ(1, end.x, end.y, end.z);
        position.needsUpdate = true;
        line.geometry.computeBoundingSphere();
        if (line.material instanceof THREE.LineDashedMaterial) line.computeLineDistances();
        return true;
      })
      .onNodeClick((node: object) => callbacks.current.onNodeClick?.((node as SimNode).id))
      .onLinkClick((link: object) => callbacks.current.onLinkClick?.((link as SimLink).id))
      .onBackgroundClick(() => callbacks.current.onBackgroundClick?.())
      .onEngineStop(() => {
        // Frame the settled layout, also while a live graph grows, until the person moves the scene.
        if (nodeMap.current.size > 0 && !touched.current) {
          fitted.current = true;
          instance.zoomToFit(reducedMotion() ? 0 : 400, 48);
        }
      });
    // The layout settles in a few seconds; with reduced motion it is computed before showing.
    instance.cooldownTime(4000);
    // Repulsion only between near nodes: separate groups stay close instead of drifting away.
    (instance.d3Force("charge") as unknown as { distanceMax: (value: number) => void } | undefined)?.distanceMax(96);
    (instance.d3Force("link") as unknown as { distance: (value: number) => void } | undefined)?.distance(24);
    if (reducedMotion()) instance.warmupTicks(300).cooldownTicks(0);
    graph.current = instance;

    // Touching the scene freezes the layout where it is (docs/DESIGN.md, section 6).
    const freeze = () => {
      touched.current = true;
      for (const node of nodeMap.current.values()) {
        if (node.x !== undefined) {
          node.fx = node.x;
          node.fy = node.y;
          node.fz = node.z;
        }
      }
    };
    element.addEventListener("pointerdown", freeze);
    const resize = new ResizeObserver(() => instance.width(element.clientWidth).height(element.clientHeight));
    resize.observe(element);

    return () => {
      cancelAnimationFrame(frame.current);
      element.removeEventListener("pointerdown", freeze);
      resize.disconnect();
      instance._destructor();
      graph.current = null;
      // A new scene starts empty: the data effect adds everything again.
      nodeMap.current.clear();
      linkMap.current.clear();
      fitted.current = false;
      touched.current = false;
    };
  }, []);

  // Data: keep the objects that exist, so nodes do not jump.
  useEffect(() => {
    const instance = graph.current;
    if (!instance) return;
    const first = nodeMap.current.size === 0;
    const wanted = new Map(nodes.map((node) => [node.id, node]));
    let changed = false;
    for (const id of [...nodeMap.current.keys()]) {
      if (!wanted.has(id)) {
        nodeMap.current.delete(id);
        changed = true;
      }
    }
    for (const node of nodes) {
      const existing = nodeMap.current.get(node.id);
      if (existing) {
        existing.name = node.name;
        existing.type = node.type;
      } else {
        const born = first || reducedMotion() ? undefined : performance.now();
        nodeMap.current.set(node.id, { ...node, born });
        changed = true;
      }
    }
    const wantedLinks = new Map(
      links.filter((link) => wanted.has(link.from) && wanted.has(link.to)).map((link) => [link.id, link]),
    );
    for (const id of [...linkMap.current.keys()]) {
      if (!wantedLinks.has(id)) {
        linkMap.current.delete(id);
        changed = true;
      }
    }
    for (const link of wantedLinks.values()) {
      const existing = linkMap.current.get(link.id);
      if (existing) {
        existing.view = link;
      } else {
        linkMap.current.set(link.id, { id: link.id, source: link.from, target: link.to, view: link });
        changed = true;
      }
    }
    if (changed) {
      // The first data is laid out before it is shown, so the scene opens almost still.
      instance.warmupTicks(first ? 120 : reducedMotion() ? 300 : 0);
      instance.graphData({ nodes: [...nodeMap.current.values()], links: [...linkMap.current.values()] });
      if (!frame.current) frame.current = requestAnimationFrame(grow);
      // Frame the first data at once; the engine frames it again when the layout settles.
      if (first && nodes.length) {
        requestAnimationFrame(() => graph.current === instance && instance.zoomToFit(0, 48));
      }
    }
  }, [nodes, links]);

  // Turning the names on or off rebuilds the node objects; positions stay.
  useEffect(() => {
    graph.current?.nodeThreeObject((node: object) => nodeObject(node));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [labels]);

  // Styles: tier changes and focus apply to the existing objects.
  useEffect(() => {
    for (const node of nodeMap.current.values()) {
      const material = node.mesh?.material as THREE.MeshLambertMaterial | undefined;
      if (material) material.opacity = !focus || focus.has(node.id) ? 1 : DIMMED;
      const label = node.label?.material as THREE.SpriteMaterial | undefined;
      if (label) label.opacity = !focus || focus.has(node.id) ? 1 : DIMMED;
    }
    for (const link of linkMap.current.values()) {
      if (!link.line) continue;
      const bright = !focus || (focus.has(link.view.from) && focus.has(link.view.to));
      styleLine(link.line, link.view, bright ? 1 : DIMMED);
    }
  });

  return <div ref={container} className="stage-graph" aria-label="Grafo 3D" role="img" />;
}
