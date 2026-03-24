# --- LOGIQUE ADMIN SECRÈTE ---
if user_actif == "admin":
    st.sidebar.markdown("---")
    admin_mode = st.sidebar.toggle("🛠️ MODE ADMIN")
    
    if admin_mode:
        page = "🛠️ PANNEAU ADMIN" # Force la page vers l'admin

# --- CONTENU DU PANNEAU ADMIN ---
if user_actif == "admin" and page == "🛠️ PANNEAU ADMIN":
    st.title("🛠️ Panneau de Contrôle Master")
    
    tab1, tab2 = st.tabs(["👥 Gérer les Logins", "📜 Logs d'Activité"])
    
    with tab1:
        st.subheader("Ajouter un nouvel accès")
        new_user = st.text_input("Nom de l'ami")
        new_pass = st.text_input("Mot de passe choisi")
        
        if st.button("CRÉER LE COMPTE"):
            # Ici, on ajoute l'utilisateur dans le dictionnaire en mémoire
            if new_user and new_pass:
                USERS[new_user] = new_pass
                st.success(f"✅ Compte créé pour {new_user} ! (Note: sera réinitialisé au redémarrage si pas sauvé sur GitHub)")
            else:
                st.error("Remplis les deux cases !")
        
        st.markdown("---")
        st.write("**Utilisateurs actuels :**")
        st.json(USERS)

    with tab2:
        st.subheader("Journal de l'usine")
        # On affiche les dossiers créés récemment pour voir qui travaille
        if os.path.exists("Output_Reels"):
            for u in os.listdir("Output_Reels"):
                st.write(f"📁 L'utilisateur **{u}** a des fichiers dans son Drive.")
