export function documentTypeLabel(type: string) {
  const labels: Record<string, string> = {
    research_paper: "研究论文",
    review_paper: "综述论文",
    thesis_or_report: "学位/报告",
    academic_like_document: "学术材料",
    non_academic: "非论文材料",
    empty_or_unreadable: "文本不可读",
    unknown: "未知类型"
  };
  return labels[type] ?? type;
}

export function domainLabel(domain: string) {
  const labels: Record<string, string> = {
    computer_science: "计算机科学",
    physics: "物理学",
    mathematics: "数学",
    chemistry: "化学",
    biology: "生物学",
    medicine: "医学",
    economics: "经济学",
    social_science: "社会科学",
    engineering: "工程",
    humanities: "人文学科",
    non_academic: "非学术",
    general: "通用科研",
    unknown: "通用科研"
  };
  return labels[domain] ?? domain;
}
