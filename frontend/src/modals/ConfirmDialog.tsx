import type { ReactNode } from "react";

type Props = {
    children?: ReactNode;
    onConfirm: () => void;
    onCancel: () => void;
}

export default function ConfirmDialog({ children, onConfirm, onCancel }: Props) {
    return (
        <div className="h-min flex flex-col">
            <div className="flex-grow">
                {children}
            </div>
            <div className="flex justify-end flex-row gap-2">
                <button onClick={onConfirm} className="btn btn-green">confirm</button>
                <button onClick={onCancel} className="btn btn-red">cancel</button>
            </div>
        </div>
    )
}