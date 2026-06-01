# DEPLOYMENT GUIDE — GitHub Pages

## Quick Deploy (5 minutes)

### Option 1: User/Org Page (`username.github.io`)

1. Create a new repo named `ChonSong.github.io` (replace with your GitHub username)
2. Add the files:

```bash
# From the host machine:
cd /tmp
git clone git@github.com:ChonSong/ChonSong.github.io.git
cd ChonSong.github.io

# Copy the built site
cp /workspace/docs/index.html ./index.html
cp -r /workspace/docs/images ./images  # if using screenshots

git add .
git commit -m "Initial GitHub Pages site — Linear design"
git push origin main
```

3. Go to `https://github.com/ChonSong/ChonSong.github.io/settings/pages`
4. Source: Deploy from a branch → Branch: `main` / `/ (root)`
5. **Done.** Site live at `https://chonsong.github.io`

### Option 2: Project Page (`github.com/user/repo`)

1. Push to any repo's `gh-pages` branch
2. GitHub auto-serves at `https://user.github.io/repo`

### Option 3: Custom Domain

Add a `CNAME` file to repo root with your domain:

```
sean.cheong.dev
```

Then add a CNAME DNS record:
- Type: CNAME
- Name: `@` or your subdomain
- Value: `ChonSong.github.io`

## Files to Deploy

```
index.html          ← Main site (everything inline: CSS, JS, fonts from Google CDN)
```

That's it. One file. No build, no dependencies.

## Verification Checklist

After deploying, verify:

- [ ] `https://chonsong.github.io` loads without errors
- [ ] Dark background renders (`#08090a`)
- [ ] Inter font with `cv01`/`ss03` OpenType features renders (check lowercase 'a' is single-story)
- [ ] Brand buttons are violet-indigo (`#5e6ad2`)
- [ ] Stats bar shows correct numbers
- [ ] All 6 project cards render
- [ ] Skills grid shows all items
- [ ] Architecture diagram renders correctly
- [ ] Footer links work
- [ ] Mobile responsive (test at 375px width)
- [ ] Scroll animations trigger on each section

## Post-Deploy Enhancements

1. **Favicon:** Generate an `SC` monogram favicon and add `<link rel="icon" ...>`
2. **Open Graph:** Add `og:title`, `og:description`, `og:image` meta tags
3. **Theme color:** Add `<meta name="theme-color" content="#08090a">` for mobile browser chrome
4. **Knowledge Graph:** Interactive graph embed (add graph files to repo)
5. **Analytics:** Plausible.io (privacy-focused, no cookie banner needed)

## Updating

To update the site after changes:

```bash
# Make edits to docs/index.html in the workspace
# Then copy and push:
cp /workspace/docs/index.html /tmp/ChonSong.github.io/index.html
cd /tmp/ChonSong.github.io
git add . && git commit -m "Update site" && git push
```
