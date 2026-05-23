type SVGProps = React.SVGProps<SVGSVGElement>;

const stroke: SVGProps = {
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.6,
  strokeLinecap: "round",
  strokeLinejoin: "round",
  viewBox: "0 0 24 24",
};

export const Icon = {
  Dashboard: () => (
    <svg {...stroke}>
      <rect x="3" y="3" width="7" height="9" rx="2" />
      <rect x="14" y="3" width="7" height="5" rx="2" />
      <rect x="14" y="12" width="7" height="9" rx="2" />
      <rect x="3" y="16" width="7" height="5" rx="2" />
    </svg>
  ),
  Forms: () => (
    <svg {...stroke}>
      <rect x="4" y="3" width="16" height="18" rx="2" />
      <path d="M8 8h8M8 12h8M8 16h5" />
    </svg>
  ),
  Tickets: () => (
    <svg {...stroke}>
      <path d="M21 10a2 2 0 0 1-2-2V7a2 2 0 0 0-2-2H7a2 2 0 0 0-2 2v1a2 2 0 0 1-2 2v4a2 2 0 0 1 2 2v1a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-1a2 2 0 0 1 2-2z" />
      <path d="M12 5v14" strokeDasharray="2 3" />
    </svg>
  ),
  Users: () => (
    <svg {...stroke}>
      <circle cx="9" cy="8" r="3" />
      <path d="M3 20c0-3 3-5 6-5s6 2 6 5" />
      <circle cx="17" cy="10" r="2.5" />
      <path d="M14 19c0-2 1.5-3.5 4-3.5s3 1.5 3 3.5" />
    </svg>
  ),
  Builder: () => (
    <svg {...stroke}>
      <path d="M3 7h18M3 12h18M3 17h12" />
      <circle cx="19" cy="17" r="2" />
    </svg>
  ),
  Search: () => (
    <svg {...stroke}>
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-3.5-3.5" />
    </svg>
  ),
  Bell: () => (
    <svg {...stroke}>
      <path d="M6 8a6 6 0 1 1 12 0c0 7 3 7 3 9H3c0-2 3-2 3-9Z" />
      <path d="M10 21a2 2 0 0 0 4 0" />
    </svg>
  ),
  Settings: () => (
    <svg {...stroke}>
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1 1.7 1.7 0 0 0-.3-1.8L4.2 7a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9c.1.6.5 1.2 1.5 1.4H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1Z" />
    </svg>
  ),
  ChevronDown: () => (
    <svg {...stroke}>
      <path d="m6 9 6 6 6-6" />
    </svg>
  ),
  X: () => (
    <svg {...stroke}>
      <path d="M18 6 6 18M6 6l12 12" />
    </svg>
  ),
  Plus: () => (
    <svg {...stroke}>
      <path d="M12 5v14M5 12h14" />
    </svg>
  ),
  Edit: () => (
    <svg {...stroke}>
      <path d="M14 4l6 6-12 12H2v-6L14 4Z" />
    </svg>
  ),
  Trash: () => (
    <svg {...stroke}>
      <path d="M4 7h16M10 11v6M14 11v6M6 7l1 13a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-13M9 7V4h6v3" />
    </svg>
  ),
  Check: () => (
    <svg {...stroke}>
      <path d="m5 12 5 5L20 7" />
    </svg>
  ),
  Filter: () => (
    <svg {...stroke}>
      <path d="M4 5h16l-6 8v5l-4 2v-7L4 5Z" />
    </svg>
  ),
  Send: () => (
    <svg {...stroke}>
      <path d="M22 2 11 13M22 2l-7 20-4-9-9-4 20-7Z" />
    </svg>
  ),
  Paperclip: () => (
    <svg {...stroke}>
      <path d="M21 12 12 21a5 5 0 0 1-7-7L14 5a3.5 3.5 0 1 1 5 5l-9 9a2 2 0 0 1-3-3l8-8" />
    </svg>
  ),
  Download: () => (
    <svg {...stroke}>
      <path d="M12 3v12M7 10l5 5 5-5M5 21h14" />
    </svg>
  ),
  Logout: () => (
    <svg {...stroke}>
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9" />
    </svg>
  ),
};
