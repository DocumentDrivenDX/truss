/** Bounded original PostgreSQL response-frame subset; not a socket/authority producer. */
export interface WireLimits {
    readonly maxFrameBytes: number;
    readonly maxFields: number;
}
export declare function decodeResponseFrame(frame: Uint8Array, limits: WireLimits): {
    readonly kind: string;
    readonly originalHex: string;
    readonly fields: readonly Readonly<Record<string, string | null>>[];
};
