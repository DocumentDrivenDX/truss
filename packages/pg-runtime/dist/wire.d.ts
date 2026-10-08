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
/** Complete-frame admission before forwarding; delivered socket chunks already exist. */
export declare class ResponseIngress {
    #private;
    readonly limits: WireLimits & {
        readonly maxTotalBytes: number;
        readonly maxFrames: number;
    };
    constructor(limits: WireLimits & {
        readonly maxTotalBytes: number;
        readonly maxFrames: number;
    });
    feed(chunk: Uint8Array, forward: (frame: Uint8Array) => void): void;
    finish(): void;
    get accounting(): Readonly<{
        bytes: number;
        frames: number;
        refused: boolean;
    }>;
}
