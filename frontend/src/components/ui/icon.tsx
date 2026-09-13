"use client";

import {
  Play,
  ListVideo,
  ThumbsUp,
  MessageCircle,
  Share2,
  BellRing,
  Flame,
  UserRound,
  Radio,
  Home,
  Rocket,
  Smartphone,
  ListChecks,
  Plus,
  ChevronRight,
  type LucideIcon,
} from "lucide-react";

const MAP: Record<string, LucideIcon> = {
  Play,
  ListVideo,
  ThumbsUp,
  MessageCircle,
  Share2,
  BellRing,
  Flame,
  UserRound,
  Radio,
  Home,
  Rocket,
  Smartphone,
  ListChecks,
  Plus,
  ChevronRight,
};

export function Icon({
  name,
  className = "h-5 w-5",
}: {
  name: string;
  className?: string;
}) {
  const Cmp = MAP[name] ?? Play;
  return <Cmp className={className} />;
}
