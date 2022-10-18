/**
 * A PNG image with transparent background and black text:
 * "External image (path unchanged)"
 * Also includes a small icon in the left side indicating
 * that it is an image.
 */
export const UNCHANGED_IMAGE =
	'data:image/png;base64,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';
