/**
 * File overview
 * Purpose: Describe authenticated account data used by the customer interface.
 * Responsibilities: Describe the profile's string-serialized credit and payment-method flag,
 *   and the wallet endpoint's numeric balance response.
 * Connections: Mirrors schemas/auth.py for profiles and api/routes/auth.py for top-ups;
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

//---top-up result: the endpoint returns a message and the updated numeric balance.---
export interface WalletTopupResponse{
    message: string
    nuovo_saldo: number
}
