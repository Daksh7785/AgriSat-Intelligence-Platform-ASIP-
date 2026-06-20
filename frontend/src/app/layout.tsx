import "./globals.css";
import { Providers } from "./providers";

export const metadata = {
  title: "AgriSense AI - Command Area Evapotranspiration & Precision Irrigation Dashboard",
  description: "An automated Remote Sensing platform mapping crop classification, moisture stress anomalies, and FAO-56 water deficits.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link
          rel="stylesheet"
          href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
          integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
          crossOrigin=""
        />
      </head>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
