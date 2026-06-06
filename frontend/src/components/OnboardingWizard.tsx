import { useState, useEffect } from "react";

import { motion, AnimatePresence } from "framer-motion";
import {
  BookOpen,
  ChevronRight,
  Clapperboard,
  FileText,
  Settings,
  Sparkles,
  X,
} from "lucide-react";

const STEPS = [
  {
    id: "welcome",
    title: "欢迎使用 ScriptForge",
    description:
      "ScriptForge 是一款 AI 驱动的小说转剧本工具。只需 5 步，即可将您的小说转换为专业剧本格式。",
    icon: Sparkles,
    action: "开始",
  },
  {
    id: "create-project",
    title: "第 1 步：创建项目",
    description:
      "首先创建一个项目，输入小说名称和基本信息。每个项目独立管理章节、角色和剧本。",
    icon: Clapperboard,
    action: "创建项目",
  },
  {
    id: "upload-chapters",
    title: "第 2 步：上传章节",
    description:
      "将小说章节粘贴或上传为 .txt/.md 文件。至少需要 3 章才能启动 AI 转换。",
    icon: FileText,
    action: "上传章节",
  },
  {
    id: "configure-model",
    title: "第 3 步：配置模型",
    description:
      "选择并配置 AI 模型提供商（Anthropic Claude 或 OpenAI）。设置 API 密钥和转换参数。",
    icon: Settings,
    action: "配置模型",
  },
  {
    id: "start-conversion",
    title: "第 4 步：开始转换",
    description:
      "启动 AI 转换管道。系统将自动分析故事结构、生成角色网络、逐章转换并组装剧本。",
    icon: Sparkles,
    action: "开始转换",
  },
  {
    id: "first-edit",
    title: "第 5 步：首次编辑",
    description:
      "转换完成后进入剧本编辑器。您可以编辑台词、调整场景、查看批注建议、保存版本。",
    icon: BookOpen,
    action: "进入编辑器",
  },
];

const STORAGE_KEY = "scriptforge_onboarding_completed";

export function OnboardingWizard() {
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState(0);


  useEffect(() => {
    const completed = localStorage.getItem(STORAGE_KEY);
    if (!completed) {
      setOpen(true);
    }
  }, []);

  const handleNext = () => {
    if (step < STEPS.length - 1) {
      setStep(step + 1);
    } else {
      finish();
    }
  };

  const handleSkip = () => {
    finish();
  };

  const finish = () => {
    localStorage.setItem(STORAGE_KEY, "true");
    setOpen(false);
  };



  if (!open) return null;

  const current = STEPS[step];
  const Icon = current.icon;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="relative w-full max-w-lg overflow-hidden rounded-2xl border border-neutral-800 bg-neutral-900 shadow-2xl"
      >
        {/* Close */}
        <button
          onClick={handleSkip}
          className="absolute right-4 top-4 rounded-lg p-1 text-neutral-500 hover:bg-neutral-800 hover:text-neutral-300"
          aria-label="跳过引导"
        >
          <X className="h-4 w-4" />
        </button>

        {/* Progress dots */}
        <div className="flex justify-center gap-2 pt-6">
          {STEPS.map((_, i) => (
            <div
              key={i}
              className={`h-1.5 rounded-full transition-all ${
                i === step
                  ? "w-6 bg-amber-500"
                  : i < step
                    ? "w-1.5 bg-amber-500/50"
                    : "w-1.5 bg-neutral-700"
              }`}
            />
          ))}
        </div>

        {/* Content */}
        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.2 }}
            className="px-8 pb-8 pt-6 text-center"
          >
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-amber-900/30">
              <Icon className="h-7 w-7 text-amber-500" />
            </div>

            <h2 className="mb-2 text-xl font-bold text-neutral-100">
              {current.title}
            </h2>
            <p className="mb-6 text-sm leading-relaxed text-neutral-400">
              {current.description}
            </p>

            <div className="flex items-center justify-center gap-3">
              {step > 0 && (
                <button
                  onClick={() => setStep(step - 1)}
                  className="rounded-lg border border-neutral-700 bg-neutral-800 px-4 py-2 text-sm text-neutral-300 transition-colors hover:bg-neutral-700"
                >
                  上一步
                </button>
              )}
              <button
                onClick={handleNext}
                className="inline-flex items-center gap-1 rounded-lg bg-amber-600 px-5 py-2 text-sm font-medium text-white transition-colors hover:bg-amber-500"
              >
                {step === STEPS.length - 1 ? "完成" : "下一步"}
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>

            <button
              onClick={handleSkip}
              className="mt-4 text-xs text-neutral-500 hover:text-neutral-400"
            >
              跳过引导
            </button>
          </motion.div>
        </AnimatePresence>
      </motion.div>
    </div>
  );
}

export function resetOnboarding() {
  localStorage.removeItem(STORAGE_KEY);
}
