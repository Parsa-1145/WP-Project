import React, { useEffect, useId, useMemo, useRef, useState } from "react";

/**
 * CustomSelect
 * - Drop-in-ish replacement for <select>
 * - Controlled via `value` + `onChange` (like a native select)
 * - Keyboard: Enter/Space open, Esc close, Up/Down navigate, Enter select, type-to-search
 * - Click outside to close
 * - Accessible roles (combobox + listbox)
 *
 * Props:
 * - id?: string
 * - name?: string
 * - value: string
 * - onChange: (eLike: { target: { name?: string; id?: string; value: string } }) => void
 * - options: Array<{ key: string; value?: string; name?: string; disabled?: boolean }>
 * - placeholder?: string
 * - disabled?: boolean
 * - className?: string        // container
 * - buttonClassName?: string  // trigger button
 * - menuClassName?: string    // dropdown menu
 * - optionClassName?: string  // option items
 * - renderLabel?: (opt) => ReactNode
 */
export function CustomSelect({
  id,
  name,
  value,
  onChange,
  options,
  placeholder = "Select…",
  disabled = false,
  className = "",
  buttonClassName = "",
  menuClassName = "",
  optionClassName = "",
  renderLabel,
}) {
  const autoId = useId();
  const selectId = id ?? `custom-select-${autoId}`;
  const listboxId = `${selectId}-listbox`;

  const rootRef = useRef(null);
  const buttonRef = useRef(null);

  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const [typeahead, setTypeahead] = useState("");
  const typeaheadTimerRef = useRef(null);

  const normalized = useMemo(() => {
    return (options ?? []).map((o) => ({
      ...o,
      _label: renderLabel ? renderLabel(o) : (o.name ?? o.value ?? o.key),
    }));
  }, [options, renderLabel]);

  const selectedIndex = useMemo(
    () => normalized.findIndex((o) => o.key === value),
    [normalized, value]
  );

  const selected = selectedIndex >= 0 ? normalized[selectedIndex] : null;

  const emitChange = (nextKey) => {
    onChange?.({
      target: {
        name,
        id: selectId,
        value: nextKey,
      },
    });
  };

  const openMenu = () => {
    if (disabled) return;
    setOpen(true);
    // set active to selected or first enabled
    const start = selectedIndex >= 0 ? selectedIndex : 0;
    const idx = findNextEnabled(normalized, start, +1, true);
    setActiveIndex(idx);
  };

  const closeMenu = () => {
    setOpen(false);
    setActiveIndex(-1);
  };

  const toggleMenu = () => {
    if (disabled) return;
    setOpen((v) => {
      const next = !v;
      if (!v && next) {
        // opening
        const start = selectedIndex >= 0 ? selectedIndex : 0;
        const idx = findNextEnabled(normalized, start, +1, true);
        setActiveIndex(idx);
      } else {
        setActiveIndex(-1);
      }
      return next;
    });
  };

  // Click outside to close
  useEffect(() => {
    const onDocMouseDown = (e) => {
      if (!open) return;
      if (rootRef.current && !rootRef.current.contains(e.target)) {
        closeMenu();
      }
    };
    document.addEventListener("mousedown", onDocMouseDown);
    return () => document.removeEventListener("mousedown", onDocMouseDown);
  }, [open]);

  // Keep active index valid if options/value changes while open
  useEffect(() => {
    if (!open) return;
    const idx = activeIndex;
    if (idx < 0 || idx >= normalized.length || normalized[idx]?.disabled) {
      const start = selectedIndex >= 0 ? selectedIndex : 0;
      setActiveIndex(findNextEnabled(normalized, start, +1, true));
    }
  }, [open, normalized, selectedIndex, activeIndex]);

  const onButtonKeyDown = (e) => {
    if (disabled) return;

    switch (e.key) {
      case "ArrowDown":
      case "Down": {
        e.preventDefault();
        if (!open) return openMenu();
        setActiveIndex((i) => findNextEnabled(normalized, i, +1, true));
        break;
      }
      case "ArrowUp":
      case "Up": {
        e.preventDefault();
        if (!open) return openMenu();
        setActiveIndex((i) => findNextEnabled(normalized, i, -1, true));
        break;
      }
      case "Home": {
        e.preventDefault();
        if (!open) openMenu();
        setActiveIndex(findNextEnabled(normalized, 0, +1, true));
        break;
      }
      case "End": {
        e.preventDefault();
        if (!open) openMenu();
        setActiveIndex(findNextEnabled(normalized, normalized.length - 1, -1, true));
        break;
      }
      case "Enter":
      case " ": {
        e.preventDefault();
        if (!open) return openMenu();
        if (activeIndex >= 0 && !normalized[activeIndex]?.disabled) {
          emitChange(normalized[activeIndex].key);
        }
        closeMenu();
        buttonRef.current?.focus();
        break;
      }
      case "Escape": {
        if (!open) return;
        e.preventDefault();
        closeMenu();
        buttonRef.current?.focus();
        break;
      }
      case "Tab": {
        // allow tab away; close menu
        closeMenu();
        break;
      }
      default: {
        // typeahead
        if (e.key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey) {
          const next = (typeahead + e.key).toLowerCase();
          setTypeahead(next);

          if (typeaheadTimerRef.current) clearTimeout(typeaheadTimerRef.current);
          typeaheadTimerRef.current = setTimeout(() => setTypeahead(""), 450);

          if (!open) openMenu();

          const found = findByPrefix(normalized, next, activeIndex);
          if (found !== -1) setActiveIndex(found);
        }
      }
    }
  };

  const onOptionMouseEnter = (idx) => {
    if (normalized[idx]?.disabled) return;
    setActiveIndex(idx);
  };

  const onOptionClick = (idx) => {
    const opt = normalized[idx];
    if (!opt || opt.disabled) return;
    emitChange(opt.key);
    closeMenu();
    buttonRef.current?.focus();
  };

  return (
    <div
      ref={rootRef}
      className={className}
      style={{ position: "relative", width: "100%" }}
    >
      {/* Hidden input so forms work like a native select */}
      {name ? <input type="hidden" name={name} value={value ?? ""} /> : null}

      <button
        id={selectId}
        ref={buttonRef}
        type="button"
        disabled={disabled}
        onClick={toggleMenu}
        onKeyDown={onButtonKeyDown}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={listboxId}
        aria-activedescendant={
          open && activeIndex >= 0 ? `${selectId}-opt-${activeIndex}` : undefined
        }
        role="combobox"
        className={buttonClassName}
        style={{
          width: "100%",
          textAlign: "left",
          borderRadius: 0, // square corners
          ...(buttonClassName ? {} : defaultButtonStyle(disabled)),
        }}
      >
        <span style={{ display: "inline-block" }}>
          {selected ? selected._label : placeholder}
        </span>
        <span
          aria-hidden="true"
          style={{
            float: "right",
            opacity: disabled ? 0.5 : 1,
            marginLeft: 12,
          }}
        >
          ▾
        </span>
      </button>

      {open && (
        <div
          role="listbox"
          id={listboxId}
          tabIndex={-1}
          className={menuClassName}
          style={{
            position: "absolute",
            zIndex: 1000,
            left: 0,
            right: 0,
            marginTop: 4,
            borderRadius: 0, // square corners
            ...(menuClassName ? {} : defaultMenuStyle()),
          }}
        >
          {normalized.map((opt, idx) => {
            const isSelected = opt.key === value;
            const isActive = idx === activeIndex;
            const isDisabled = !!opt.disabled;

            return (
              <div
                key={opt.key}
                id={`${selectId}-opt-${idx}`}
                role="option"
                aria-selected={isSelected}
                aria-disabled={isDisabled}
                onMouseEnter={() => onOptionMouseEnter(idx)}
                onMouseDown={(e) => e.preventDefault()} // prevent losing focus before click
                onClick={() => onOptionClick(idx)}
                className={optionClassName}
                style={{
                  borderRadius: 0, // square corners on options
                  ...(optionClassName ? {} : defaultOptionStyle(isActive, isSelected, isDisabled)),
                }}
              >
                {opt._label}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function findNextEnabled(options, startIndex, direction, wrap) {
  if (!options.length) return -1;
  let i = Number.isFinite(startIndex) ? startIndex : 0;

  // clamp start for first call
  if (i < 0) i = direction > 0 ? 0 : options.length - 1;
  if (i >= options.length) i = direction > 0 ? options.length - 1 : 0;

  for (let steps = 0; steps < options.length; steps++) {
    const opt = options[i];
    if (opt && !opt.disabled) return i;

    i += direction;
    if (i < 0) {
      if (!wrap) return -1;
      i = options.length - 1;
    } else if (i >= options.length) {
      if (!wrap) return -1;
      i = 0;
    }
  }
  return -1;
}

function findByPrefix(options, prefix, fromIndex) {
  if (!options.length) return -1;
  const start = Math.max(0, Math.min(options.length - 1, fromIndex ?? 0));
  const p = prefix.toLowerCase();

  // search forward, wrapping
  for (let pass = 0; pass < 2; pass++) {
    const begin = pass === 0 ? start : 0;
    const end = pass === 0 ? options.length : start;

    for (let i = begin; i < end; i++) {
      const opt = options[i];
      if (opt?.disabled) continue;
      const label = String(opt.name ?? opt.value ?? opt.key).toLowerCase();
      if (label.startsWith(p)) return i;
    }
  }

  return -1;
}

function defaultButtonStyle(disabled) {
  return {
    border: "1px solid #ccc",
    padding: "10px 12px",
    background: disabled ? "#f5f5f5" : "#fff",
    cursor: disabled ? "not-allowed" : "pointer",
    lineHeight: 1.2,
  };
}

function defaultMenuStyle() {
  return {
    border: "1px solid #ccc",
    background: "#fff",
    maxHeight: 240,
    overflowY: "auto",
  };
}

function defaultOptionStyle(isActive, isSelected, isDisabled) {
  return {
    padding: "10px 12px",
    cursor: isDisabled ? "not-allowed" : "pointer",
    opacity: isDisabled ? 0.5 : 1,
    background: isActive ? "#eee" : isSelected ? "#f6f6f6" : "#fff",
    userSelect: "none",
  };
}