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
    const headings = chapter.sections
      .map((section) => document.getElementById(section.id))
      .filter((element): element is HTMLElement => element !== null);
    const observer = new IntersectionObserver(
      (entries) => {
        const seen = entries.find((entry) => entry.isIntersecting);
        if (seen) setCurrent(seen.target.id);
      },
      { rootMargin: "-64px 0px -70% 0px" },
    );
    headings.forEach((heading) => observer.observe(heading));
    return () => observer.disconnect();
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
              <Link to={`/guida/${previous.slug}`} className="guide-pager-link">
                <span className="settings-title">Precedente</span>
                {previous.title}
              </Link>
            ) : (
              <span />
            )}
            {next && (
              <Link to={`/guida/${next.slug}`} className="guide-pager-link guide-pager-next">
                <span className="settings-title">Successivo</span>
                {next.title}
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
