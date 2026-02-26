import React, { createContext, useCallback, useContext, useMemo, useState } from "react";
import Modal from "./Modal";


type ModalId = string;

type ModalApi = {
  openNewModal: (node: React.ReactNode) => ModalId;
  close: (id: ModalId) => void;
  closeTop : () => void;
};

const Ctx = createContext<ModalApi | null>(null);
function uid(): ModalId {
  return Math.random().toString(36).slice(2);
}

export function ModalProvider({ children }: { children: React.ReactNode }) {
  const [stack, setStack] = useState<Array<{ id: ModalId; node: React.ReactNode }>>([]);
  
  const close = useCallback((id: ModalId) => {
    setStack((prev) => prev.filter((m) => m.id !== id));
  }, []);

  const open = useCallback<ModalApi["openNewModal"]>((node) => {
    const id = uid();
    setStack((prev) => [...prev, { id, node }]);
    return id
  }, []);
  const closeTop = useCallback(() => {
    setStack((prev) => {
      if (prev.length === 0) return prev;
      return prev.slice(0, -1);
    });
  }, []);

  const api = useMemo<ModalApi>(() => ({ openNewModal: open, close, closeTop }), [open, close, closeTop]);

  return (
    <Ctx.Provider value={api}>
      {children}
      {stack.map((node)=>{
        return(
          <Modal key={node.id} close={()=>{close(node.id)}}>
            {node.node}
          </Modal>
        )
      })}
    </Ctx.Provider>
  );
}

export function useModal() {
  const v = useContext(Ctx);
  if (!v) throw new Error("useModal must be used inside ModalProvider");
  return v;
}