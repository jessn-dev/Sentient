import Navbar from '@/components/Navbar';
import './globals.css';

export default function RootLayout({ children }: { children: React.ReactNode }) {
    return (
        <html lang="en">
        <body className="bg-gray-50 min-h-screen">
        <Navbar />
        {children}
        </body>
        </html>
    );
}