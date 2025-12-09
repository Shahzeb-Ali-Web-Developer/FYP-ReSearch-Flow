# Database Setup Instructions

## Saved Articles Table

To enable the save articles and notes functionality, you need to create the `saved_articles` table in your Supabase database.

### Steps:

1. **Open Supabase Dashboard**
   - Go to https://app.supabase.com
   - Select your project

2. **Navigate to SQL Editor**
   - Click on "SQL Editor" in the left sidebar
   - Click "New query"

3. **Run the SQL Script**
   - Copy the contents of `saved_articles_schema.sql`
   - Paste it into the SQL editor
   - Click "Run" or press Ctrl+Enter

4. **Verify Table Creation**
   - Go to "Table Editor" in the left sidebar
   - You should see `saved_articles` table listed
   - Verify the columns match:
     - `id` (uuid)
     - `user_id` (uuid)
     - `paper_id` (text)
     - `title` (text)
     - `notes` (text, nullable)
     - `created_at` (timestamp)
     - `updated_at` (timestamp)

5. **Verify RLS Policies**
   - Go to "Authentication" > "Policies"
   - Select `saved_articles` table
   - You should see 4 policies:
     - Users can view their own saved articles
     - Users can insert their own saved articles
     - Users can update their own saved articles
     - Users can delete their own saved articles

### Testing

After setup, test the functionality:
1. Log in to the application
2. Search for a paper
3. Click on a paper to open the detail panel
4. Click the "Save" button (MessageSquare icon)
5. The button should change to "Saved" with a bookmark icon
6. Click "Notes" to add/edit notes
7. Verify the article appears in your saved articles

### Troubleshooting

If you encounter issues:
- Make sure RLS is enabled on the table
- Verify the policies are correctly set up
- Check that users are authenticated before saving
- Check browser console for any error messages

