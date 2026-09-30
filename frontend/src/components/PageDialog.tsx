import { useEffect, useRef, useState } from "react";
import { Icon } from "./Icon";
import { tr } from "../i18n/i18n";

const SCALE = 2;

export interface PageMark {
  bbox: [number, number, number, number];
}

/** The page of the manual as an image, with the cited segments outlined when their position is known. */
export function PageDialog({
  manualId,
  page,
  marks,
  onClose,
}: {
  manualId: string;
  page: number;
  marks: PageMark[];
  onClose: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [size, setSize] = useState<{ width: number; height: number } | null>(null);
  // Removing the element closes the dialog; closing it here would report a close the person did not ask for.
  useEffect(() => {
    const element = dialog.current;
    if (element && !element.open) element.showModal?.();
  }, []);
  const src = `/api/manuals/${encodeURIComponent(manualId)}/pages/${page}.png?scale=${SCALE}`;
  return (
    <dialog ref={dialog} className="page-dialog" onClose={onClose} aria-label={tr("Pagina {page} del manuale", { page })}>
      <div className="page-dialog-frame">
        <div className="page-dialog-head">
          <h2 className="t-large strong">{tr("Pagina {page}", { page })}</h2>
          <button type="button" className="button button-secondary button-icon" aria-label={tr("Chiudi")} onClick={onClose}>
            <Icon name="x" />
          </button>
        </div>
        <div className="page-image">
          <img
            src={src}
            alt={tr("Pagina {page} del manuale", { page })}
            onLoad={(event) =>
              setSize({ width: event.currentTarget.naturalWidth, height: event.currentTarget.naturalHeight })
            }
          />
          {size &&
            marks.map((mark, index) => {
              const [x0, y0, x1, y1] = mark.bbox;
              return (
                <span
                  key={index}
                  className="page-mark"
                  style={{
                    left: x0 * SCALE,
                    top: y0 * SCALE,
                    width: (x1 - x0) * SCALE,
                    height: (y1 - y0) * SCALE,
                  }}
                />
              );
            })}
        </div>
        {marks.length === 0 && <p className="message t-small">{tr("La posizione del testo citato non è nota: è evidenziata solo la pagina.")}</p>}
      </div>
    </dialog>
  );
}
