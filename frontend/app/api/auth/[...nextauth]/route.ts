import NextAuth from "next-auth"
import AzureADProvider from "next-auth/providers/azure-ad"
import GoogleProvider from "next-auth/providers/google"

const providers = []

if (process.env.AUTH_PROVIDER === 'google') {
    providers.push(
        GoogleProvider({
            clientId: process.env.GOOGLE_CLIENT_ID || "",
            clientSecret: process.env.GOOGLE_CLIENT_SECRET || "",
        })
    )
} else {
    // Default to Microsoft
    providers.push(
        AzureADProvider({
            clientId: process.env.AZURE_AD_CLIENT_ID || "",
            clientSecret: process.env.AZURE_AD_CLIENT_SECRET || "",
            tenantId: process.env.AZURE_AD_TENANT_ID,
        })
    )
}

const handler = NextAuth({
    providers: providers,
    callbacks: {
        async session({ session, token }) {
            // Pass token info to session if needed for backend calls
            return session
        },
    },
    pages: {
        signIn: '/login', // Use our custom Premium Login UI
    },
    // Ensure we can deploy behind reverse proxy if needed, though localhost works fine
})

export { handler as GET, handler as POST }
