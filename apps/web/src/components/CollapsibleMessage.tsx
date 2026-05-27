import type { ReactNode } from "react";
import { useLayoutEffect, useRef, useState } from "react";

export function CollapsibleMessage({
  collapsedHeight = 360,
  children
}: {
  collapsedHeight?: number;
  children: ReactNode;
}) {
  const contentRef = useRef<HTMLDivElement>(null);
  const [expanded, setExpanded] = useState(false);
  const [collapsible, setCollapsible] = useState(false);

  useLayoutEffect(
    function measureCollapsibleContent() {
      const element = contentRef.current;
      if (!element) return;
      const measuredElement = element;

      function update() {
        setCollapsible(measuredElement.scrollHeight > collapsedHeight + 8);
      }

      update();
      if (typeof ResizeObserver === "undefined") return;
      const observer = new ResizeObserver(update);
      observer.observe(measuredElement);
      return function disconnectObserver() {
        observer.disconnect();
      };
    },
    [collapsedHeight, children]
  );

  return (
    <div className="collapsibleMessage">
      {collapsible ? (
        <button
          type="button"
          className="messageExpandButton"
          onClick={() => setExpanded((current) => !current)}
        >
          {expanded ? "收起" : "展开全文"}
        </button>
      ) : null}
      <div
        ref={contentRef}
        className={`messageFoldBody ${collapsible && !expanded ? "collapsed" : ""}`}
        style={collapsible && !expanded ? { maxHeight: collapsedHeight } : undefined}
      >
        {children}
      </div>
    </div>
  );
}
