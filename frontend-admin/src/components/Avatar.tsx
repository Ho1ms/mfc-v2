import { initials } from "@/lib/status";

interface Props {
  name?: string | null;
  size?: "sm" | "md" | "lg";
  bg?: string;
  className?: string;
}

export function Avatar({ name, size = "md", bg, className }: Props) {
  const sizeCls = size === "sm" ? "sm" : size === "lg" ? "lg" : "";
  const style: React.CSSProperties | undefined = bg
    ? { background: bg, color: "#fff", boxShadow: "inset 0 0 0 2px rgba(255,255,255,.18)" }
    : undefined;
  return (
    <div className={`avatar ${sizeCls} ${className ?? ""}`.trim()} style={style}>
      {initials(name)}
    </div>
  );
}
