import React, { type ReactNode } from "react";
import { createPortal } from "react-dom";

type Props = {
  children?: ReactNode;
  close: () => void;
};

export default function Modal({ children, close }: Props) {

  const root = document.getElementById("root");
  if (!root) return null;

  return createPortal(
    <div
      className="fixed inset-0 z-50 w-screen h-screen m-0 bg-neutral-900/60 flex justify-center items-center"
      onClick={close}
    >
      <div
        className="max-w-80 sm:max-w-150 min-w-100 h-min p-4 bg-[var(--c-surface)]  border-1 border-[var(--c-border)] relative"
        onClick={(e) => e.stopPropagation()}
      >
        {children}
      </div>
    </div>,
    root
  );
}

