import React from "react";

export const DienMayXanhLogo = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    viewBox="0 0 200 48"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={`h-10 w-auto ${props.className || ""}`}
    {...props}
  >
    <circle cx="24" cy="24" r="20" fill="#fff100" />
    <path
      d="M24 10c1.1 0 2 .9 2 2s-.9 2-2 2-2-.9-2-2 .9-2 2-2zm-5 16h3v8h4v-8h3v-4h-10v4zm7-8h-4c-2.2 0-4 1.8-4 4v3h3v-3c0-.6.4-1 1-1h4c.6 0 1 .4 1 1v3h3v-3c0-2.2-1.8-4-4-4z"
      fill="#0088dd"
    />
    <text
      x="54"
      y="24"
      fill="#ffffff"
      fontFamily="Arial, Helvetica, sans-serif"
      fontSize="16"
      fontWeight="700"
    >
      dien may
    </text>
    <text
      x="126"
      y="24"
      fill="#fff100"
      fontFamily="Arial, Helvetica, sans-serif"
      fontSize="20"
      fontWeight="900"
      letterSpacing="0.5"
    >
      XANH
    </text>
  </svg>
);

export const TheGioiDiDongLogo = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    viewBox="0 0 120 30"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={`h-6 w-auto ${props.className || ""}`}
    {...props}
  >
    <rect width="120" height="30" rx="4" fill="#ffd400" />
    <circle cx="18" cy="15" r="10" fill="#333" />
    <path d="M18 10v10M15 15h6" stroke="#ffd400" strokeWidth="2" />
    <text x="34" y="20" fill="#333333" fontSize="10" fontWeight="700">
      The Gioi Di Dong
    </text>
  </svg>
);

export const BachHoaXanhLogo = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    viewBox="0 0 120 30"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={`h-6 w-auto ${props.className || ""}`}
    {...props}
  >
    <rect width="120" height="30" rx="4" fill="#4caf50" />
    <text x="12" y="19" fill="#ffd400" fontSize="11" fontWeight="700">
      Bach Hoa XANH
    </text>
  </svg>
);

export const TopZoneLogo = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    viewBox="0 0 100 30"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={`h-6 w-auto ${props.className || ""}`}
    {...props}
  >
    <rect width="100" height="30" rx="4" fill="#000000" />
    <text x="25" y="19" fill="#ffffff" fontSize="12" fontWeight="700">
      top zone
    </text>
  </svg>
);
