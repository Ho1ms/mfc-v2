type SVGProps = React.SVGProps<SVGSVGElement>;

const s: SVGProps = {
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.6,
  strokeLinecap: "round",
  strokeLinejoin: "round",
  viewBox: "0 0 24 24",
};

export const Icon = {
  Home: () => (
    <svg {...s}>
      <path d="m3 12 9-9 9 9M5 10v10h14V10" />
    </svg>
  ),
  Plus: () => (
    <svg {...s}>
      <path d="M12 5v14M5 12h14" />
    </svg>
  ),
  History: () => (
    <svg {...s}>
      <path d="M3 12a9 9 0 1 0 3-6.7L3 8" />
      <path d="M3 3v5h5M12 7v5l3 3" />
    </svg>
  ),
  Monitor: () => (
    <svg {...s}>
      <rect x="3" y="4" width="18" height="13" rx="2" />
      <path d="M8 21h8M12 17v4" />
    </svg>
  ),
  FAQ: () => (
    <svg {...s}>
      <circle cx="12" cy="12" r="9" />
      <path d="M9.5 9a2.5 2.5 0 1 1 3.5 2.3c-.7.3-1 1-1 1.7M12 17h.01" />
    </svg>
  ),
  Profile: () => (
    <svg {...s}>
      <circle cx="12" cy="8" r="4" />
      <path d="M4 21c0-4 4-7 8-7s8 3 8 7" />
    </svg>
  ),
  Search: () => (
    <svg {...s}>
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-3.5-3.5" />
    </svg>
  ),
  Bell: () => (
    <svg {...s}>
      <path d="M6 8a6 6 0 1 1 12 0c0 7 3 7 3 9H3c0-2 3-2 3-9Z" />
      <path d="M10 21a2 2 0 0 0 4 0" />
    </svg>
  ),
  Check: () => (
    <svg {...s}>
      <path d="m5 12 5 5L20 7" />
    </svg>
  ),
  ChevronRight: () => (
    <svg {...s}>
      <path d="m9 6 6 6-6 6" />
    </svg>
  ),
  ChevronDown: () => (
    <svg {...s}>
      <path d="m6 9 6 6 6-6" />
    </svg>
  ),
};
