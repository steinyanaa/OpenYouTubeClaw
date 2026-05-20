export function buildHydratedInboxMessages(messages, speculations) {
  if (!Array.isArray(speculations)) {
    return messages;
  }

  const activeDomains = new Set(
    speculations
      .filter((item) => item && item.domain && (!item.status || item.status === "active"))
      .map((item) => item.domain),
  );

  const nextMessages = messages.filter((message) => {
    const type = message?.type || "interest.probe";
    if (type !== "interest.probe") {
      return true;
    }
    return message.domain && activeDomains.has(message.domain);
  });

  const existingDomains = new Set(
    nextMessages
      .filter((message) => (message?.type || "interest.probe") === "interest.probe" && message?.domain)
      .map((message) => message.domain),
  );

  for (const item of speculations) {
    if (!item || (item.status && item.status !== "active") || !item.domain) {
      continue;
    }
    if (existingDomains.has(item.domain)) {
      continue;
    }
    nextMessages.push({
      type: "interest.probe",
      domain: item.domain,
      reason: item.reason || "",
      specifics: Array.isArray(item.specifics) ? item.specifics : [],
    });
    existingDomains.add(item.domain);
  }

  return nextMessages;
}
