export const NormalizationType = Object.freeze({
	TITLE_CASE: 'title_case',
	SENTENCE_CASE: 'sentence_case',
	LOWER_CASE: 'lower_case',
	UPPER_CASE: 'upper_case',
	NONE: 'none',
});

const submissionDateFormat = {
    locale: undefined,
    options: {
        year: 'numeric',month: 'long',day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    },
    showRelative: true,
};

export function normalizeString(str, type = NormalizationType.TITLE_CASE) {
	const text = String(str ?? '').replace(/_/g, ' ').trim();
	switch (type) {
		case NormalizationType.NONE:
			return text;
		case NormalizationType.LOWER_CASE:
			return text.toLowerCase();
		case NormalizationType.UPPER_CASE:
			return text.toUpperCase();
		case NormalizationType.SENTENCE_CASE:
			return text ? text[0].toUpperCase() + text.slice(1).toLowerCase() : text;
		case NormalizationType.TITLE_CASE:
		default:
			return text.toLowerCase().replace(/\b\w/g, c => c.toUpperCase());
	}
}
export function formatDate(value, config = submissionDateFormat) {
	if (!value)
		return 'Unknown';
	
	const date = new Date(value);
	if (Number.isNaN(date.getTime()))
		return String(value);
	
	const formatted = new Intl.DateTimeFormat(config.locale, config.options).format(date);
	if (!config.showRelative)
		return formatted;
	
	const diffMs = date.getTime() - Date.now();
	const absMs = Math.abs(diffMs);
	const units = [
		['year', 365 * 24 * 60 * 60 * 1000],
		['month', 30 * 24 * 60 * 60 * 1000],
		['week', 7 * 24 * 60 * 60 * 1000],
		['day', 24 * 60 * 60 * 1000],
		['hour', 60 * 60 * 1000],
		['minute', 60 * 1000],
	];
	
	for (const [unit, size] of units) {
		if (absMs >= size) {
			const rtf = new Intl.RelativeTimeFormat(config.locale, { numeric: 'auto' });
			const amount = Math.round(diffMs / size);
			return `${formatted} (${rtf.format(amount, unit)})`;
		}
	}
	
	return `${formatted} (just now)`;
}