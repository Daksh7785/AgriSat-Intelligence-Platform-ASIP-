import "./globals.css";
import { Providers } from "./providers";

export const metadata = {
  title: "AgriSense AI — Satellite Intelligence Platform",
  description: "ISRO-grade satellite crop intelligence: FAO-56 precision irrigation, multi-spectral NDVI/NDWI mapping, Gemini AI Copilot, and global weather analytics.",
  keywords: "agrisense, satellite, agriculture, NDVI, FAO-56, irrigation, crop intelligence",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        {/* Leaflet CSS */}
        <link
          rel="stylesheet"
          href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
          integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
          crossOrigin=""
        />
        {/* Google Fonts — Inter + JetBrains Mono */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;700&display=swap"
          rel="stylesheet"
        />
        {/* Meta */}
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="theme-color" content="#060D18" />
      </head>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
