import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

// Junta classes CSS condicionais e resolve conflitos do Tailwind; a última classe prevalece.
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
