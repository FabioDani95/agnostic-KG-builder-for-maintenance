import { type MouseEvent, useEffect, useState } from "react";
import { Link, Navigate, NavLink, useParams } from "react-router-dom";
import { Icon } from "../components/Icon";
import { Shell } from "../components/Shell";
import { type Block, GUIDE } from "../help/guide";

function Body({ blocks }: { blocks: Block[] }) {
  return (
    <>
      {blocks.map((block, index) =>
        typeof block === "string" ? (
          <p key={index}>{block}</p>
        ) : (
          <ul key={index}>
            {block.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        ),
      )}
    </>
  );
}

/**
 * The guide, as in the help of DigiFactor: chapters on the left, the page in the middle, «In questa
 * pagina» on the right following the reading. Every chapter has its own address.
 */
export function Guide() {
  const { chapter: slug } = useParams();
  const index = GUIDE.findIndex((chapter) => chapter.slug === slug);
  const chapter = GUIDE[index];
  const [current, setCurrent] = useState<string>("");

  useEffect(() => {
    if (!chapter) return;
    setCurrent(chapter.sections[0]?.id ?? "");
    document.querySelector(".content")?.scrollTo({ top: 0 });
    // The section being read: the last heading above the top of the page, the last one at the bottom.
    const page = document.querySelector<HTMLElement>(".content");
    if (!page) return;
    const follow = () => {
      const top = page.getBoundingClientRect().top + 96;
      const atBottom = page.scrollTop + page.clientHeight >= page.scrollHeight - 4;
      let reading = chapter.sections[0]?.id ?? "";
      for (const section of chapter.sections) {
        const heading = document.getElementById(section.id);
        if (heading && heading.getBoundingClientRect().top <= top) reading = section.id;
      }
      setCurrent(atBottom ? chapter.sections[chapter.sections.length - 1].id : reading);
    };
    page.addEventListener("scroll", follow, { passive: true });
    return () => page.removeEventListener("scroll", follow);
  }, [chapter]);

  if (!chapter) return <Navigate to={`/guida/${GUIDE[0].slug}`} replace />;

  const jump = (event: MouseEvent<HTMLAnchorElement>, id: string) => {
    event.preventDefault();
    const reduced = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    document.getElementById(id)?.scrollIntoView({ behavior: reduced ? "auto" : "smooth", block: "start" });
    setCurrent(id);
  };
  const previous = GUIDE[index - 1];
  const next = GUIDE[index + 1];

  return (
    <Shell trail={[{ to: `/guida/${GUIDE[0].slug}`, label: "Guida" }]} title={chapter.title}>
      <div className="guide">
        <nav className="guide-menu" aria-label="Capitoli della guida">
          <div className="guide-menu-inner">
            <p className="settings-title">Capitoli</p>
            <ul>
              {GUIDE.map((item) => (
                <li key={item.slug}>
                  <NavLink to={`/guida/${item.slug}`} className="guide-link">
                    <Icon name={item.icon} />
                    {item.title}
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>
        </nav>

        <article className="guide-article">
          <h2 className="guide-title">{chapter.title}</h2>
          <p className="guide-lead">{chapter.lead}</p>
          {chapter.sections.map((section) => (
            <section key={section.id} id={section.id} className="guide-section">
              <h3>{section.heading}</h3>
              <Body blocks={section.body} />
            </section>
          ))}
          <nav className="guide-pager" aria-label="Capitolo precedente e successivo">
            {previous ? (
              <Link to={`/guida/${previous.slug}`} className="guide-pager-link" aria-label={`Capitolo precedente: ${previous.title}`}>
                <Icon name="arrow-left" size={18} />
                <span>{previous.title}</span>
              </Link>
            ) : (
              <span />
            )}
            {next && (
              <Link to={`/guida/${next.slug}`} className="guide-pager-link guide-pager-next" aria-label={`Capitolo successivo: ${next.title}`}>
                <Icon name="arrow-right" size={18} />
                <span>{next.title}</span>
              </Link>
            )}
          </nav>
        </article>

        <nav className="guide-toc" aria-label="In questa pagina">
          <div className="guide-menu-inner">
            <p className="settings-title">In questa pagina</p>
            <ul>
              {chapter.sections.map((section) => (
                <li key={section.id}>
                  <a
                    href={`#${section.id}`}
                    className="guide-toc-link"
                    aria-current={section.id === current ? "location" : undefined}
                    onClick={(event) => jump(event, section.id)}
                  >
                    {section.heading}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </nav>
      </div>
    </Shell>
  );
}
