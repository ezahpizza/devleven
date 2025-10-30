// E.164 phone number validation
export const isValidPhoneNumber = (phone: string): boolean => {
  const e164Regex = /^\+[1-9]\d{1,14}$/;
  return e164Regex.test(phone);
};

export const isValidClientName = (name: string): boolean => {
  return name.trim().length >= 2 && name.trim().length <= 255;
};

export const sanitizePhoneNumber = (phone: string): string => {
  // Remove all non-digit characters except leading +
  return phone.replace(/(?!^\+)\D/g, "");
};
