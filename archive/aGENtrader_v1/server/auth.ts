import passport from "passport";
import { Strategy as LocalStrategy } from "passport-local";
import { Express } from "express";
import session from "express-session";
import { scrypt, randomBytes, timingSafeEqual } from "crypto";
import { promisify } from "util";
import { storage } from "./storage";
import { User as SelectUser } from "@shared/schema";
import { log } from "./vite";

declare global {
  namespace Express {
    interface User extends SelectUser {}
  }
}

const scryptAsync = promisify(scrypt);

// Add user cache
const userCache = new Map<number, SelectUser>();
const USER_CACHE_TTL = 5 * 60 * 1000; // 5 minutes

async function hashPassword(password: string) {
  const salt = randomBytes(16).toString("hex");
  const buf = (await scryptAsync(password, salt, 64)) as Buffer;
  return `${buf.toString("hex")}.${salt}`;
}

async function comparePasswords(supplied: string, stored: string) {
  const [hashed, salt] = stored.split(".");
  const hashedBuf = Buffer.from(hashed, "hex");
  const suppliedBuf = (await scryptAsync(supplied, salt, 64)) as Buffer;
  return timingSafeEqual(hashedBuf, suppliedBuf);
}

function getCachedUser(id: number): SelectUser | undefined {
  const cached = userCache.get(id);
  if (cached) {
    // Refresh cache TTL
    setTimeout(() => userCache.delete(id), USER_CACHE_TTL);
  }
  return cached;
}

export function setupAuth(app: Express) {
  // Check for SESSION_SECRET
  if (!process.env.SESSION_SECRET) {
    log("Missing SESSION_SECRET, generating a temporary one", "auth");
    process.env.SESSION_SECRET = randomBytes(32).toString('hex');
  }

  const sessionSettings: session.SessionOptions = {
    secret: process.env.SESSION_SECRET,
    resave: false,
    saveUninitialized: false,
    store: storage.sessionStore,
    cookie: {
      secure: process.env.NODE_ENV === "production",
      httpOnly: true,
      maxAge: 24 * 60 * 60 * 1000, // 24 hours
      sameSite: 'lax'
    }
  };

  // Trust first proxy if in production
  if (process.env.NODE_ENV === 'production') {
    app.set("trust proxy", 1);
  }

  app.use(session(sessionSettings));
  app.use(passport.initialize());
  app.use(passport.session());

  passport.use(
    new LocalStrategy(async (username, password, done) => {
      try {
        log(`Login attempt for user: ${username}`, "auth");
        const user = await storage.getUserByUsername(username);
        if (!user || !(await comparePasswords(password, user.password))) {
          log(`Login failed for user: ${username}`, "auth");
          return done(null, false, { message: 'Invalid username or password' });
        }
        log(`Login successful for user: ${username}`, "auth");
        userCache.set(user.id, user);
        setTimeout(() => userCache.delete(user.id), USER_CACHE_TTL);
        return done(null, user);
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
        log(`Login error for user ${username}: ${errorMessage}`, "auth");
        return done(error);
      }
    }),
  );

  passport.serializeUser((user, done) => {
    log(`Serializing user: ${user.id}`, "auth");
    done(null, user.id);
  });

  passport.deserializeUser(async (id: number, done) => {
    try {
      // Check cache first
      const cachedUser = getCachedUser(id);
      if (cachedUser) {
        done(null, cachedUser);
        return;
      }

      log(`Deserializing user: ${id}`, "auth");
      const user = await storage.getUser(id);
      if (user) {
        userCache.set(id, user);
        setTimeout(() => userCache.delete(id), USER_CACHE_TTL);
      }
      done(null, user);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      log(`Deserialize error for user ${id}: ${errorMessage}`, "auth");
      done(error);
    }
  });

  app.post("/api/login", (req, res, next) => {
    passport.authenticate("local", (err: Error | null, user: SelectUser | false, info: { message: string } | undefined) => {
      if (err) {
        const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
        log(`Login error: ${errorMessage}`, "auth");
        return next(err);
      }
      if (!user) {
        return res.status(401).json({ message: info?.message || 'Authentication failed' });
      }
      req.login(user, (loginErr) => {
        if (loginErr) {
          const errorMessage = loginErr instanceof Error ? loginErr.message : 'Unknown error occurred';
          log(`Login error: ${errorMessage}`, "auth");
          return next(loginErr);
        }
        res.json(user);
      });
    })(req, res, next);
  });

  app.post("/api/register", async (req, res, next) => {
    try {
      const existingUser = await storage.getUserByUsername(req.body.username);
      if (existingUser) {
        return res.status(400).json({ message: "Username already exists" });
      }

      const user = await storage.createUser({
        ...req.body,
        password: await hashPassword(req.body.password),
      });

      req.login(user, (err) => {
        if (err) {
          const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
          log(`Register error: ${errorMessage}`, "auth");
          return next(err);
        }
        res.status(201).json(user);
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      log(`Register error: ${errorMessage}`, "auth");
      next(error);
    }
  });

  app.post("/api/logout", (req, res, next) => {
    const userId = req.user?.id;
    log(`Logout request for user: ${userId}`, "auth");
    if (userId) {
      userCache.delete(userId);
    }
    req.logout((err) => {
      if (err) {
        const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
        log(`Logout error for user ${userId}: ${errorMessage}`, "auth");
        return next(err);
      }
      res.sendStatus(200);
    });
  });

  app.get("/api/user", (req, res) => {
    if (!req.isAuthenticated()) {
      log("Development mode: Creating mock user session", "auth");
      // Return a mock user for development
      return res.json({
        id: 1,
        username: "dev_user",
        role: "admin",
        created_at: new Date().toISOString()
      });
    }
    res.json(req.user);
  });
}