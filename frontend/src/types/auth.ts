/**
 * File overview
 * Purpose: Describe authenticated account data used by the customer interface.
 * Responsibilities: Describe account and wallet responses using decimal strings for balances,
 *   together with the profile's payment-method flag.
 * Connections: Mirrors the profile and wallet response models in schemas/auth.py;
 *   Profile consumes GET /api/auth/me and POST /api/auth/wallet/topup.
 */

//---profile contract: match the authenticated account response.---
export interface UserProfile{
    codicefiscale: string
    email: string
    ruolo: string
    saldo_crediti: string //its a string because the backend serializes Decimal values like this
    has_payment_method: boolean
}

// --- Top-up result: return a message and the updated balance as a decimal string. ---
export interface WalletTopupResponse{
    message: string
    nuovo_saldo: string
}
