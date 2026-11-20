import './globals.css';
import Link from 'next/link';
export const metadata={title:'InterviewAI — Your Personal AI Interviewer',description:'Spoken AI interview practice for software and AI placements'};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en"><body><header className="border-b border-[#1f2530] bg-[#090b10]/95 sticky top-0 z-40"><div className="container h-16 flex items-center justify-between"><Link href="/" className="font-bold tracking-tight text-lg">Interview<span className="text-slate-400">AI</span></Link><nav className="flex gap-2 text-sm"><Link className="btn btn-ghost" href="/dashboard">Dashboard</Link><Link className="btn btn-primary" href="/setup">Start Interview</Link></nav></div></header>{children}</body></html>}
