import NextAuth, { type NextAuthConfig } from "next-auth";
import Credentials from "next-auth/providers/credentials";
import GitHub from "next-auth/providers/github";
import Google from "next-auth/providers/google";
import { devAccountId, enabledProviders, type ProviderId } from "@/lib/auth-config";

const MAX_DEV_NAME_LENGTH = 40;

const devProvider = Credentials({
  id: "dev",
  name: "Dev",
  credentials: { name: { label: "Ad" } },
  authorize(credentials) {
    const name = String(credentials?.name ?? "")
      .trim()
      .slice(0, MAX_DEV_NAME_LENGTH);
    const id = devAccountId(name);
    return id ? { id, name } : null;
  },
});

const PROVIDERS: Record<ProviderId, NextAuthConfig["providers"][number]> = {
  github: GitHub,
  google: Google,
  dev: devProvider,
};

declare module "next-auth" {
  interface Session {
    /** "<provider>:<provider account id>" — the user's identity in the Just Sport API. */
    accountId?: string;
  }
}

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: enabledProviders(process.env).map((id) => PROVIDERS[id]),
  session: { strategy: "jwt" },
  pages: { signIn: "/signin" },
  callbacks: {
    jwt({ token, account }) {
      if (account) token.accountId = `${account.provider}:${account.providerAccountId}`;
      return token;
    },
    session({ session, token }) {
      if (typeof token.accountId === "string") session.accountId = token.accountId;
      return session;
    },
  },
});
