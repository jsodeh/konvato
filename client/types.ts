/**
 * TypeScript interfaces for betslip conversion frontend data structures.
 * 
 * This file defines the type contracts for:
 * - API request/response objects
 * - Bookmaker selection and conversion results
 * - Form validation schemas
 */

// API Request/Response Interfaces

/**
 * Request payload for betslip conversion API
 */
export interface ConversionRequest {
  betslipCode: string;
  sourceBookmaker: string;
  destinationBookmaker: string;
}

/**
 * Individual betting selection data
 */
export interface Selection {
  game: string;
  market: string;
  odds: number;
  originalOdds: number;
  status: 'converted' | 'partial' | 'unavailable';
  homeTeam?: string;
  awayTeam?: string;
  league?: string;
  eventDate?: string;
}

/**
 * Response from betslip conversion API
 */
export interface ConversionResponse {
  success: boolean;
  betslipCode?: string;
  selections: Selection[];
  warnings: string[];
  processingTime: number;
  partialConversion?: boolean;
  errorMessage?: string;
}

/**
 * Bookmaker configuration data
 */
export interface Bookmaker {
  id: string;
  name: string;
  baseUrl: string;
  supported: boolean;
  logoUrl?: string;
}

/**
 * Response from bookmakers API endpoint
 */
export interface BookmakersResponse {
  bookmakers: Bookmaker[];
}

// Frontend Component Props and State Interfaces

/**
 * Props for BookmakerSelector component
 */
export interface BookmakerSelectorProps {
  value: string;
  onChange: (value: string) => void;
  bookmakers: Bookmaker[];
  label: string;
  disabled?: boolean;
  error?: string;
}

/**
 * Props for ResultsDisplay component
 */
export interface ResultsDisplayProps {
  result: ConversionResponse;
  onNewConversion: () => void;
  onCopyBetslipCode?: (code: string) => void;
}

/**
 * Props for LoadingSpinner component
 */
export interface LoadingSpinnerProps {
  message?: string;
  size?: 'small' | 'medium' | 'large';
}

/**
 * Props for ErrorMessage component
 */
export interface ErrorMessageProps {
  message: string;
  onRetry?: () => void;
  onDismiss?: () => void;
}

// Form State and Validation Interfaces

/**
 * Main application state for betslip conversion
 */
export interface AppState {
  betslipCode: string;
  sourceBookmaker: string;
  destinationBookmaker: string;
  result: ConversionResponse | null;
  loading: boolean;
  error: string | null;
  bookmakers: Bookmaker[];
  bookmarkersLoading: boolean;
}

/**
 * Form validation errors
 */
export interface ValidationErrors {
  betslipCode?: string;
  sourceBookmaker?: string;
  destinationBookmaker?: string;
  general?: string;
}

/**
 * Form validation result
 */
export interface ValidationResult {
  isValid: boolean;
  errors: ValidationErrors;
}

// Utility Types

/**
 * API error response structure
 */
export interface ApiError {
  message: string;
  code?: string;
  details?: Record<string, any>;
}

/**
 * HTTP response wrapper
 */
export interface ApiResponse<T> {
  data?: T;
  error?: ApiError;
  status: number;
}

/**
 * Configuration for API client
 */
export interface ApiConfig {
  baseUrl: string;
  timeout: number;
  retries: number;
}

// Form Validation Schema Types

/**
 * Validation rule for form fields
 */
export interface ValidationRule {
  required?: boolean;
  minLength?: number;
  maxLength?: number;
  pattern?: RegExp;
  custom?: (value: string) => string | null;
}

/**
 * Validation schema for conversion form
 */
export interface ConversionFormSchema {
  betslipCode: ValidationRule;
  sourceBookmaker: ValidationRule;
  destinationBookmaker: ValidationRule;
}

// Event Handler Types

/**
 * Form submission event handler
 */
export type FormSubmitHandler = (event: React.FormEvent<HTMLFormElement>) => void;

/**
 * Input change event handler
 */
export type InputChangeHandler = (event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => void;

/**
 * Button click event handler
 */
export type ButtonClickHandler = (event: React.MouseEvent<HTMLButtonElement>) => void;

// Constants and Enums

/**
 * Supported bookmaker IDs
 */
export enum BookmakerIds {
  BET9JA = 'bet9ja',
  SPORTYBET = 'sportybet',
  BETWAY = 'betway',
  BET365 = 'bet365'
}

/**
 * Selection status types
 */
export enum SelectionStatus {
  CONVERTED = 'converted',
  PARTIAL = 'partial',
  UNAVAILABLE = 'unavailable'
}

/**
 * API endpoint paths
 */
export enum ApiEndpoints {
  CONVERT = '/api/convert',
  BOOKMAKERS = '/api/bookmakers'
}

/**
 * Loading states
 */
export enum LoadingState {
  IDLE = 'idle',
  LOADING = 'loading',
  SUCCESS = 'success',
  ERROR = 'error'
}

// Type Guards

/**
 * Type guard to check if an object is a valid ConversionResponse
 */
export function isConversionResponse(obj: any): obj is ConversionResponse {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    typeof obj.success === 'boolean' &&
    Array.isArray(obj.selections) &&
    Array.isArray(obj.warnings) &&
    typeof obj.processingTime === 'number'
  );
}

/**
 * Type guard to check if an object is a valid Selection
 */
export function isSelection(obj: any): obj is Selection {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    typeof obj.game === 'string' &&
    typeof obj.market === 'string' &&
    typeof obj.odds === 'number' &&
    typeof obj.originalOdds === 'number' &&
    ['converted', 'partial', 'unavailable'].includes(obj.status)
  );
}

/**
 * Type guard to check if an object is a valid Bookmaker
 */
export function isBookmaker(obj: any): obj is Bookmaker {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    typeof obj.id === 'string' &&
    typeof obj.name === 'string' &&
    typeof obj.baseUrl === 'string' &&
    typeof obj.supported === 'boolean'
  );
}